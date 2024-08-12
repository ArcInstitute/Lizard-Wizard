#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import sys
import argparse
## 3rd party
import openai


# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Summarize pipeline log files"
epi = """DESCRIPTION:
Summarize log files from the pipeline using an LLM.
Warnings and errors are prioritized
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument("log_file", type=str, nargs="+",
                    help="log file to summarize.")
parser.add_argument("-o", "--output-dir", type=str, default="output",
                    help="Output directory.")
parser.add_argument("-m", "--model", type=str, default="gpt-4o-mini",
                    choices=["gpt-4o-mini", "gpt-4o"],
                    help="openai model to use.")

# functions
def summarize_log(log_content: str, client: openai.Client, max_tokens: int=1000) -> str:
    """
    Use the openai client to summarize the log content.
    Args:
        log_content: the log content to summarize
        client: openai client
        max_tokens: max tokens for the completion
    Returns:
        str: the LLM-generated summary
    """
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize the following log file content, prioritizing warnings and errors."},
            {"role": "user", "content": log_content}
        ],
        max_tokens=max_tokens
    )
    return completion.choices[0].message.content

def write_blank_files(log_files: list, output_dir: str):
    """
    Write out blank output files for each log file.
    Args:
        log_files: list of log files
        output_dir: output directory
    """
    for log_file in log_files:
        outfile_base = os.path.splitext(os.path.basename(log_file))[0] + "_summary.md"
        outfile = os.path.join(output_dir,  outfile_base)
        open(outfile, "w").close()
        print(f"  Blank summary written to {outfile}", file=sys.stderr)

# functions
def main(args):
    # Output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Check for OPENAI_API_KEY
    if os.getenv("OPENAI_API_KEY") is None:
        print("WARNING: No OPENAI_API_KEY environment variable", file=sys.stderr)
        # write out blank output files
        write_blank_files(args.log_files, args.output_dir)
        exit()

    # Create openai client
    client = openai.Client()
    
    # Process each log file
    all_summaries = ""
    for log_file in args.log_file:
        print(f"Processing {log_file}", file=sys.stderr)

        # Read the log file
        with open(log_file) as f:
            log_content = f.read()
        
        # Summarize the log file
        summary = summarize_log(log_content, openai)
        
        # Write the summary to a file
        outfile_base = os.path.splitext(os.path.basename(log_file))[0] + "_summary.md"
        outfile = os.path.join(args.output_dir,  outfile_base)
        with open(outfile, "w") as f:
            f.write(summary + "\n")
        print(f"  Summary written to {outfile}", file=sys.stderr)

        # Append to summaries
        all_summaries += f"--- {outfile_base} ---\n" + summary + "\n\n"
    
    # summarize all summaries
    print("Summarizing all log file summaries", file=sys.stderr)
    summary = summarize_log(all_summaries, openai, max_tokens=1500)
    outfile = os.path.join(args.output_dir, "final_summary.md")
    with open(outfile, "w") as f:
        f.write(summary + "\n")
    print(f"  Summary written to {outfile}", file=sys.stderr)

    
## script main
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
