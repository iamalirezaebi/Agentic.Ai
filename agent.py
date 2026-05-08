import ollama
import json
import time
import os
import math

MODEL = "llama3:latest"


# -----------------------------------
# LLM CALL
# -----------------------------------
def call_llama(messages):
    response = ollama.chat(
        model=MODEL,
        messages=messages,
        options={
            "temperature": 0.2
        }
    )
    return response["message"]["content"]


# -----------------------------------
# TOOLS
# -----------------------------------
def tool_calculator(expression):
    try:
        allowed = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "sqrt": math.sqrt
        }
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"CALCULATOR_ERROR: {str(e)}"


def tool_read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:6000]  # limit size
    except Exception as e:
        return f"READ_FILE_ERROR: {str(e)}"


def tool_list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"LIST_FILES_ERROR: {str(e)}"


def tool_write_note(filename, content):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"NOTE_SAVED: {filename}"
    except Exception as e:
        return f"WRITE_NOTE_ERROR: {str(e)}"


# -----------------------------------
# SYSTEM PROMPT
# -----------------------------------
SYSTEM_PROMPT = """
You are an offline autonomous AI agent running locally on a laptop.

You must reason using this loop:
PLAN -> ACTION -> REFLECT.

Available tools:
1. calculator(expression)
2. read_file(path)
3. list_files(path)
4. write_note(filename|content)

Rules:
- Respond ONLY in valid JSON.
- Do not use markdown.
- Use tools when needed.
- If you already know the answer, set action to "none".
- If using write_note, put input in this format:
  "filename|content"

Output JSON format:
{
  "plan": "...",
  "action": "calculator" or "read_file" or "list_files" or "write_note" or "none",
  "tool_input": "...",
  "final_answer": "...",
  "reflection": "..."
}
"""


# -----------------------------------
# JSON PARSER
# -----------------------------------
def parse_json(text):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return None


# -----------------------------------
# TOOL EXECUTOR
# -----------------------------------
def execute_tool(action, tool_input):
    if action == "calculator":
        return tool_calculator(tool_input)

    elif action == "read_file":
        return tool_read_file(tool_input)

    elif action == "list_files":
        return tool_list_files(tool_input if tool_input else ".")

    elif action == "write_note":
        try:
            filename, content = tool_input.split("|", 1)
            return tool_write_note(filename.strip(), content.strip())
        except:
            return "WRITE_NOTE_ERROR: tool_input must be 'filename|content'"

    return None


# -----------------------------------
# AGENT LOOP
# -----------------------------------
def run_agent(task, max_steps=6):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]

    print("\nAGENT STARTED\n")

    for step in range(max_steps):
        print(f"\nSTEP {step + 1}")

        reply = call_llama(messages)
        print("\nMODEL OUTPUT:\n", reply)

        data = parse_json(reply)

        if not data:
            print("\nERROR: Could not parse JSON from model output.")
            return

        action = data.get("action", "none")
        tool_input = data.get("tool_input", "")
        final_answer = data.get("final_answer", "")

        if final_answer:
            print("\nFINAL ANSWER:\n")
            print(final_answer)
            return

        tool_result = execute_tool(action, tool_input)

        messages.append({"role": "assistant", "content": reply})

        if tool_result is not None:
            print("\nTOOL RESULT:\n", tool_result)
            messages.append({
                "role": "user",
                "content": f"Tool result:\n{tool_result}\nContinue reasoning and respond with JSON only."
            })
        else:
            messages.append({
                "role": "user",
                "content": "No tool used. Continue reasoning and respond with JSON only."
            })

        time.sleep(0.3)

    print("\nWARNING: Max steps reached.")


# -----------------------------------
# RUN EXAMPLES
# -----------------------------------
if __name__ == "__main__":
    run_agent("Read Agentic_AI_Autonomous_Intelligence_for_Complex_GoalsA_Comprehensive_Survey.pdf in the current folder and tell me what you see.")
