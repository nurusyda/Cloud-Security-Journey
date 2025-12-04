"""
YOLO.py - Local AI Council with Qwen3-VL-4B Included
Uses 3 models: Qwen3-4B-Thinking (Thinker), DeepSeek-R1-8B (DeepSeek), Qwen3-VL-4B (Vision)
Vision role uses qwen3-vl-4b for text or image queries (add image URL in prompt for vision tasks)
100% local via LM Studio

Updates:
- Simplified output formatting for easier reading (shorter responses, clear sections, no dense text).
- After each session (debate/teach/ask), added option to continue the conversation on the same topic with follow-up prompts.
"""

import requests
import time

# ============================================================================
# COUNCIL MEMBERS - Hardcoded to your models
# ============================================================================

COUNCIL_MEMBERS = {
    "thinker": {
        "name": "Thinker",
        "model": "qwen/qwen3-4b-thinking-2507",
        "system_prompt": "Respond directly, concisely, and clearly. Use short sentences and simple words. Avoid complex explanations.",
        "color": "\033[94m"
    },
    "deepseek": {
        "name": "DeepSeek",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "system_prompt": "Respond directly, concisely, and clearly. Use short sentences and simple words. Avoid complex explanations.",
        "color": "\033[91m"
    },
    "vision": {
        "name": "Vision",
        "model": "qwen/qwen3-vl-4b",
        "system_prompt": "Respond directly, concisely, and clearly. Use short sentences and simple words. Avoid complex explanations.",
        "color": "\033[92m"
    }
}

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# ============================================================================
# CORE
# ============================================================================

def call_llm(member_id: str, message: str, context: str = "") -> str:
    member = COUNCIL_MEMBERS[member_id]
    full_msg = f"{context}\n\n{message}" if context else message

    payload = {
        "model": member["model"],
        "messages": [
            {"role": "system", "content": member["system_prompt"]},
            {"role": "user", "content": full_msg}
        ],
        "temperature": 0.75,
        "max_tokens": 300  # Limit for shorter, clearer responses
    }

    try:
        r = requests.post(LM_STUDIO_URL, json=payload, timeout=240)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {e}"

def print_colored(member_id: str, text: str):
    color = COUNCIL_MEMBERS[member_id]["color"]
    reset = "\033[0m"
    name = COUNCIL_MEMBERS[member_id]["name"]
    # Simplified printing: shorter box, add line breaks in text for readability
    formatted_text = "\n".join(line for line in text.split("\n") if line.strip())  # Remove empty lines
    print(f"\n{color}--- {name} ---{reset}")
    print(formatted_text + "\n")

def check_connection():
    try:
        r = requests.get("http://localhost:1234/v1/models", timeout=5)
        if r.status_code == 200:
            models = [m["id"] for m in r.json()["data"]]
            print("LM Studio connected!")
            print("Loaded models:", ", ".join(models))
            return True
    except:
        print("Cannot connect to LM Studio on port 1234")
    return False

# ============================================================================
# CONTINUE CONVERSATION FUNCTION
# ============================================================================

def continue_conversation(topic: str, mode: str, previous_context: str = ""):
    while True:
        print(f"\nCurrent topic: {topic}")
        print("Enter follow-up question/comment (or 'back' to menu):")
        followup = input("> ").strip()
        if followup.lower() == 'back':
            break

        if mode == "debate":
            debate(followup, previous_context=previous_context)
        elif mode == "teach":
            teach(followup, previous_context=previous_context)
        elif mode == "ask_one":
            ask_one(followup, previous_context=previous_context)

# ============================================================================
# MODES - Simplified for readability
# ============================================================================

def debate(topic: str, previous_context: str = ""):
    print(f"\n★ Debate: {topic}\n")

    # Phase 1: Initial responses
    print("Initial Responses:\n")
    responses = {}
    context = previous_context + f"\nResponses to '{topic}':\n"
    for mid in COUNCIL_MEMBERS:
        print(f"{COUNCIL_MEMBERS[mid]['name']} thinking...")
        resp = call_llm(mid, topic, context)
        responses[mid] = resp
        print_colored(mid, resp)
        context += f"{COUNCIL_MEMBERS[mid]['name']}: {resp}\n"
        time.sleep(0.6)

    # Phase 2: Cross-responses (shortened)
    print("Cross-Responses:\n")
    cross_comments = {}
    for mid in COUNCIL_MEMBERS:
        print(f"{COUNCIL_MEMBERS[mid]['name']} reviewing...")
        comment_prompt = f"Review these responses to '{topic}':\n{context}\nComment briefly on each by name. Note interesting points or corrections."
        comment = call_llm(mid, comment_prompt)
        cross_comments[mid] = comment
        print_colored(mid, comment)
        time.sleep(0.6)

    # Phase 3: Conclusion
    print("Conclusion:\n")
    conclusion_context = context + "\nComments:\n" + "\n".join(f"{COUNCIL_MEMBERS[mid]['name']}: {cross_comments[mid]}" for mid in COUNCIL_MEMBERS)
    conclusion_prompt = f"Summarize key points from above in a short, clear conclusion."
    conclusion = call_llm("thinker", conclusion_prompt, conclusion_context)
    print_colored("thinker", "Final Conclusion:\n" + conclusion)

    continue_conversation(topic, "debate", context)

def teach(topic: str, previous_context: str = ""):
    print(f"\n📚 Teach: {topic}\n")

    context = previous_context
    for mid in COUNCIL_MEMBERS:
        resp = call_llm(mid, topic, context)
        print_colored(mid, resp)
        context += f"{COUNCIL_MEMBERS[mid]['name']}: {resp}\n"

    continue_conversation(topic, "teach", context)

def ask_one(topic: str = None, previous_context: str = ""):
    print("\nWho to ask?")
    for i, k in enumerate(COUNCIL_MEMBERS, 1):
        print(f"   {i}. {COUNCIL_MEMBERS[k]['name']}")
    c = input("\nChoice (1-3): ").strip()
    if c in "123":
        mid = list(COUNCIL_MEMBERS)[int(c)-1]
        if topic is None:
            topic = input(f"\nAsk {COUNCIL_MEMBERS[mid]['name']}: ")
        print("\nThinking...")
        ans = call_llm(mid, topic, previous_context)
        print_colored(mid, ans)
        continue_conversation(topic, "ask_one", previous_context + f"{COUNCIL_MEMBERS[mid]['name']}: {ans}\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("""
--- YOLO.py ---
3 Local Models: Thinker, DeepSeek, Vision
Ask anything. Vision handles images (add URL).
Simple, clear responses.
""")

    if not check_connection():
        input("\nStart LM Studio → load models → server on 1234 → then run me again")
        return

    while True:
        print("\nMenu:")
        print("1. Debate")
        print("2. Teach")
        print("3. Ask One")
        print("4. Test Connection")
        print("5. Exit")
        choice = input("> ").strip()

        if choice == "1":
            topic = input("\nTopic to debate: ")
            if topic: debate(topic)
        elif choice == "2":
            topic = input("\nTopic to learn: ")
            if topic: teach(topic)
        elif choice == "3":
            ask_one()
        elif choice == "4":
            check_connection()
            input("Press Enter...")
        elif choice == "5":
            print("\nDone. Bye!")
            break

if __name__ == "__main__":
    main()
