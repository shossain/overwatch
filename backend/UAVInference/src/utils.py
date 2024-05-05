# Import Required Libraries
import math

from tankbuster import bust


def get_number_of_frames(metadata: list[dict]) -> int:
    # Get the number of the frames from the metadata
    return len(metadata)


def calculate_distance(point1: list[float], point2: list[float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def detect_state_change(
    previous_context: list[dict], current_context: list[dict]
) -> str:
    # Extract types of objects from both frames
    prev_types = set(obj["prompt"] for obj in previous_context)
    current_types = set(obj["prompt"] for obj in current_context)

    # Check if the number of objects and their types are consistent
    if prev_types == current_types:
        return "no_change"
    elif prev_types < current_types:
        return "positive"
    elif prev_types > current_types:
        return "negative"


def analyze_frames(previous_frame: list[dict], current_frame: list[dict]):
    # Initialize lists to store descriptions of changes and patterns
    changes = []
    patterns = []

    # Extract objects from previous and current frames
    prev_objects = {obj["id"]: obj for obj in previous_frame}
    curr_objects = {obj["id"]: obj for obj in current_frame}

    # Identify added, removed, and overlapping objects
    added_objects = [
        curr_objects[name] for name in curr_objects if name not in prev_objects
    ]
    removed_objects = [
        prev_objects[name] for name in prev_objects if name not in curr_objects
    ]
    overlapping_objects = [
        curr_objects[name] for name in curr_objects if name in prev_objects
    ]

    # Describe added and removed objects
    for obj in added_objects:
        changes.append(
            f"New {obj['prompt']} '{obj['id']}' detected at centroid {obj['centroid']}"
        )

    for obj in removed_objects:
        changes.append(f"{obj['prompt']} '{obj['id']}' removed from the scene")

    # Identify and describe patterns among overlapping objects
    for obj in overlapping_objects:
        matching_prev_obj = prev_objects[obj["id"]]
        if obj["prompt"] == "smoke":
            patterns.append(f"smoke detected at centroid {obj['centroid']}")
        else:
            if obj["centroid"] == matching_prev_obj["centroid"]:
                patterns.append(
                    f"{obj['prompt']} '{obj['id']}' remained stationary at centroid {obj['centroid']}"
                )
            else:
                displacement = [
                    round(curr - prev, 2)
                    for curr, prev in zip(
                        obj["centroid"], matching_prev_obj["centroid"]
                    )
                ]
                patterns.append(
                    f"{obj['prompt']} '{obj['id']}' moved by displacement {displacement}"
                )

    return changes, patterns


def analyze_scene(previous_frame: list[dict:any], current_frame: list[dict:any]):
    """Analyze the changes between two frames."""
    new_objects = []
    removed_objects = []
    unchanged_objects = []

    # Iterate through current frame to find new and unchanged objects
    for current_obj in current_frame:
        matched = False
        # Check if current object exists in previous frame
        for prev_obj in previous_frame:
            if current_obj["id"] == prev_obj["id"]:
                matched = True
                # Check if centroid and radius are the same
                if (
                    current_obj["centroid"] == prev_obj["centroid"]
                    and current_obj["size"] == prev_obj["size"]
                ):
                    unchanged_objects.append(current_obj)
                break
        # If no match found, it's a new object
        if not matched:
            new_objects.append(current_obj)

    # Find removed objects by comparing with previous frame
    for prev_obj in previous_frame:
        found = False
        for current_obj in current_frame:
            if prev_obj["id"] == current_obj["id"]:
                found = True
                break
        if not found:
            removed_objects.append(prev_obj)

    # Generate descriptions of changes
    descriptions = []
    if new_objects:
        descriptions.append("New objects detected:")
        for obj in new_objects:
            descriptions.append(
                f"- id {obj['id']} of type {obj['prompt']} at centroid {obj['centroid']} with size {obj['size']}"
            )
    if removed_objects:
        descriptions.append("\nRemoved objects:")
        for obj in removed_objects:
            descriptions.append(
                f"- id {obj['id']} of type {obj['prompt']} at centroid {obj['centroid']} with size {obj['size']}"
            )
    if unchanged_objects:
        descriptions.append("\nUnchanged objects:")
        for obj in unchanged_objects:
            descriptions.append(
                f"- id {obj['id']} of type {obj['prompt']} at centroid {obj['centroid']} with radius {obj['size']}"
            )

    # Look for specific events or patterns
    for obj in current_frame:
        if obj["prompt"] == "vehicle":
            nearby_smoke = []
            for smoke in current_frame:
                if smoke["prompt"] == "smoke":
                    distance = calculate_distance(obj["centroid"], smoke["centroid"])
                    if distance <= 10:  # Arbitrary distance threshold
                        nearby_smoke.append(smoke)
            if nearby_smoke:
                descriptions.append(f"\nVehicle {obj['id']} detected near smoke:")
                for smoke in nearby_smoke:
                    descriptions.append(
                        f"- Smoke {smoke['name']} at centroid {smoke['centroid']} with radius {smoke['radius']}"
                    )

    return descriptions


def find_tank_probability(img_path: str) -> dict:
    output_dict = bust(img_path, network="ResNet")
    return output_dict


if __name__ == "__main__":
    previous_frame = [
        {"id": 1, "centroid": [760, 223], "size": 88929.0, "prompt": "smoke"},
        {"id": 2, "centroid": [591, 399], "size": 18337.0, "prompt": "vehicle"},
        {"id": 3, "centroid": [423, 322], "size": 692.0, "prompt": "vehicle"},
    ]

    current_frame = [
        {"id": 2, "centroid": [591, 399], "size": 18337.0, "prompt": "vehicle"},
        {"id": 3, "centroid": [423, 322], "size": 692.0, "prompt": "vehicle"},
    ]

    descriptions = analyze_frames(previous_frame, current_frame)
    for desc in descriptions:
        print(desc)
        print()
    descriptions = analyze_scene(previous_frame, current_frame)
    for desc in descriptions:
        print(desc)
