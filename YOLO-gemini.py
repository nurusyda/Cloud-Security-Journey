"""
YOLO.py - Local AI Council
Restored original prompt logic to preserve model content.
Only updates visual presentation (boxes, bolding) and fixes cut-offs.
"""

import requests
import time
import re
import textwrap

# --- Council Members ---
COUNCIL_MEMBERS = {
    "thinker": {
        "name": "Thinker",
        "model": "qwen/qwen3-4b-thinking-2507",
        "system_prompt": "",
        "color": "\033[94m"  # Blue
    },
    "deepseek": {
        "name": "DeepSeek",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "system_prompt": "",
        "color": "\033[91m"  # Red
    },
    "vision": {
        "name": "Vision",
        "model": "qwen/qwen3-vl-4b",
        "system_prompt": "",
        "color": "\033[92m"  # Green
    }
}

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# --- Presentation Logic (Python Side Only) ---

def format_markdown_to_terminal(text):
    """Converts markdown **bold** to terminal bold without changing text."""
    BOLD = "\033[1m"
    RESET = "\033[0m"
    # Convert **text** to real bold
    text = re.sub(r'\*\*(.*?)\*\*', f'{BOLD}\\1{RESET}', text)
    # Convert headers (### Text) to real bold
    text = re.sub(r'^(#+\s?)(.*)', f'{BOLD}\\2{RESET}', text, flags=re.MULTILINE)
    return text

def print_box(text, title, color_code):
    """Wraps the text in a box for readability."""
    reset = "\033[0m"
    width = 80
    horizontal = "─" * width
    
    # Apply visual formatting (does not change content)
    formatted_text = format_markdown_to_terminal(text)
    
    print(f"\n{color_code}┌{horizontal}┐")
    print(f"│ {title:<{width-2}} │")
    print(f"├{horizontal}┤{reset}")
    
    # Simple paragraph splitting
    paragraphs = formatted_text.split('\n')
    for para in paragraphs:
        wrapped_lines = textwrap.wrap(para, width=width-4)
        if not wrapped_lines:
            print(f"{color_code}│{reset} {' ':<{width-2}} {color_code}│{reset}")
        for line in wrapped_lines:
            # Calculate padding manually to handle invisible color codes
            clean_line = re.sub(r'\033\[[0-9;]*m', '', line)
            padding = width - 4 - len(clean_line)
            print(f"{color_code}│{reset} {line}{' ' * padding} {color_code}│{reset}")

    print(f"{color_code}└{horizontal}┘{reset}\n")

def clean_response(text: str) -> str:
    """Removes thinking process to show only the final answer."""
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    if "<think>" in text and "</think>" not in text:
        return "[Error: Model ran out of tokens while thinking. Please increase Context Length in LM Studio.]"
    return text.strip()

# --- Core Logic ---

def call_llm(member_id: str, message: str, context: str = "") -> str:
    member = COUNCIL_MEMBERS[member_id]
    
    # --- REVERTED TO YOUR ORIGINAL PROMPT LOGIC ---
    # We only append the simple structure request, exactly as you had it.
    structured_message = f"{message}\n\nStructure your answer with bullets or short paragraphs for easy reading."
    full_msg = f"{context}\n\n{structured_message}" if context else structured_message

    payload = {
        "model": member["model"],
        "messages": [
            {"role": "system", "content": member["system_prompt"]},
            {"role": "user", "content": full_msg}
        ],
        "temperature": 0.1,  # Kept your original low temperature
        "max_tokens": 4096   # CRITICAL FIX: Increased token limit so it doesn't cut off
    }

    try:
        r = requests.post(LM_STUDIO_URL, json=payload, timeout=300)
        r.raise_for_status()
        # Clean the <think> tags before returning
        return clean_response(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return f"Error: {e}"

def check_connection():
    try:
        r = requests.get("http://localhost:1234/v1/models", timeout=5)
        return r.status_code == 200
    except:
        return False

# --- Modes ---

def debate(topic: str, previous_context: str = ""):
    print(f"\n★ DEBATE TOPIC: {topic}\n")
    context = previous_context + f"\nResponses to '{topic}':\n"

    for mid in COUNCIL_MEMBERS:
        name = COUNCIL_MEMBERS[mid]['name']
        print(f" > {name} is thinking...")
        resp = call_llm(mid, topic, context)
        print_box(resp, name, COUNCIL_MEMBERS[mid]['color'])
        context += f"{name}: {resp}\n"
        time.sleep(0.5)

    print("\n--- CROSS EXAMINATION ---\n")
    for mid in COUNCIL_MEMBERS:
        name = COUNCIL_MEMBERS[mid]['name']
        print(f" > {name} is reviewing others...")
        # Simple review prompt, largely matching your original logic
        prompt = f"Review responses to '{topic}':\n{context}\nComment briefly on each by name."
        comment = call_llm(mid, prompt)
        print_box(comment, f"{name} Reviews", COUNCIL_MEMBERS[mid]['color'])

    continue_conversation(topic, "debate", context)

def teach(topic: str, previous_context: str = ""):
    print(f"\n📚 TEACHING: {topic}\n")
    context = previous_context
    for mid in COUNCIL_MEMBERS:
        name = COUNCIL_MEMBERS[mid]['name']
        print(f" > {name} is preparing lesson...")
        resp = call_llm(mid, topic, context)
        print_box(resp, name, COUNCIL_MEMBERS[mid]['color'])
        context += f"{name}: {resp}\n"
    continue_conversation(topic, "teach", context)

def ask_one(topic: str = None, previous_context: str = ""):
    print("\n--- SELECT MEMBER ---")
    keys = list(COUNCIL_MEMBERS.keys())
    for i, k in enumerate(keys, 1):
        print(f" {i}. {COUNCIL_MEMBERS[k]['name']}")
    
    c = input("\nChoice (1-3): ").strip()
    if c in "123":
        mid = keys[int(c)-1]
        name = COUNCIL_MEMBERS[mid]['name']
        if topic is None:
            topic = input(f"\nAsk {name}: ")
        
        print(f"\n > {name} is thinking...")
        ans = call_llm(mid, topic, previous_context)
        print_box(ans, name, COUNCIL_MEMBERS[mid]['color'])
        continue_conversation(topic, "ask_one", previous_context + f"{name}: {ans}\n")

def continue_conversation(topic: str, mode: str, previous_context: str = ""):
    while True:
        print(f"Context: {topic}")
        followup = input("Follow-up (or 'back'): ").strip()
        if followup.lower() == 'back': break
        
        if mode == "debate": debate(followup, previous_context)
        elif mode == "teach": teach(followup, previous_context)
        elif mode == "ask_one": ask_one(followup, previous_context)

def main():
    print("\n=== YOLO.py AI COUNCIL ===")
    if not check_connection():
        print("Error: Connect to LM Studio first.")
        return

    while True:
        print("\n1. Debate  2. Teach  3. Ask One  4. Exit")
        choice = input("> ").strip()
        if choice == "1": debate(input("Topic: "))
        elif choice == "2": teach(input("Topic: "))
        elif choice == "3": ask_one()
        elif choice == "4": break

if __name__ == "__main__":
    main()
