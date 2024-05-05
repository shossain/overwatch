# Import Required Packages
from src.persona import Persona
from src.utils import (
    calculate_distance,
    detect_state_change,
    analyze_frames,
    analyze_scene,
    get_number_of_frames
)
import json
import time
import sys
import os

previous_context = []

def run_pipeline(metadata: list[list[dict]]) -> str:
    # Create a persona object for summarization
    summarizer = Persona(
        name="summarization",
        prompt_path="inference_prompt.txt",
        model_name="gpt-4-turbo",
        temperature=0.8
    )

    # Create a persona object for modification
    modifier = Persona(
        name="modification",
        prompt_path="modifier.txt",
        model_name="gpt-4-turbo",
        temperature=0.8
    )

    # Preprocess metadata
    num_frames = get_number_of_frames(metadata)
    qual_log = ["" for _ in range(num_frames)]
    historical_context = []

    start_time = time.time()
    for i in range(num_frames):
        current_frame = metadata[i]
        if i == 0:
            # Format Prompt Arguments
            system_args = {
                'historical_context': historical_context
            }
            user_args = {
                'summarization': current_frame
            }

            formatted = summarizer.format_prompt(args = system_args, system = True)
            response_1, _ = summarizer.chat(
                    system_args = system_args,
                    prompt_args = user_args
            )
            historical_context.append(current_frame)
            qual_log[i] = response_1
        if i > 0 and historical_context:
            previous_frame = historical_context[-1]
            changes, patterns = analyze_frames(previous_frame, current_frame)
            state_change = detect_state_change(previous_frame, current_frame)
            scene_changes_qualitative = analyze_scene(previous_frame, current_frame)
            if state_change != "no_change":
                # Format Prompt Arguments
                system_args = {
                    'historical_context': historical_context
                }
                user_args = {
                    'summarization': current_frame
                }

                formatted = summarizer.format_prompt(args = system_args, system = True)
                response_1, _ = summarizer.chat(
                     system_args = system_args,
                     prompt_args = user_args
                )

                system_args_modifier = {}
                user_args_modifier = {
                    'scene_changes_qualitative': scene_changes_qualitative,
                    'changes': changes,
                    'patterns': patterns
                }

                formatted = modifier.format_prompt(args = user_args_modifier, system = False)
                # response_2, _ = modifier.chat( 
                #     system_args = system_args_modifier,
                #     prompt_args = user_args_modifier
                # )

                qual_log[i] = response_1

                historical_context.append(current_frame)

    end_time = time.time()
    print(f"Total Inference Time: {end_time - start_time} seconds")
    return qual_log

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py filename")
    else:
        filename = sys.argv[1]

    metadata = json.load(open(filename, "r"))
    qual_log = run_pipeline(metadata)
    for i, log in enumerate(qual_log):
        if log != "":
            print(f"Frame {i}: {log}")

    base_name = os.path.basename(filename).split(".")[0]
    output_filename = os.path.join("../files/{}".format(base_name), base_name + "_qualitative_log.json")
    with open(output_filename, "w") as f:
        json.dump(qual_log, f)
    print("Qualitative log saved to output directory.")
