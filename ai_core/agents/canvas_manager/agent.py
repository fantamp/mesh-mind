from google.adk.agents import LlmAgent
from ai_core.common.config import settings

# Import tools
from ai_core.tools.elements import fetch_elements
from ai_core.tools.canvas_ops import (
    get_current_canvas_info,
    set_canvas_name,
    create_canvas_frame,
    set_frame_name,
    list_canvas_frames,
    add_element_to_frame,
    remove_element_from_frame,
    set_element_name,
    create_element,
    set_canvas_name,
    edit_element,
)

def create_agent():
    return LlmAgent(
        name="canvas_manager",
        model=settings.GEMINI_MODEL_SMART,
        description="Agent responsible for managing and organizing the canvas",
        instruction="""
- You are the Canvas Manager. Canvas is a virtual working space where users organize their thoughts and information.
- Your role and goal is:
    - to help the user organize their thoughts and information on the Canvas.
    - to observe the Canvas and frames to examine the contents.

- You have access to the following tools:
    - fetch_elements: List elements in a frame
    - list_canvas_frames: List all frames in the current canvas
    - create_canvas_frame: Create a new frame
    - set_frame_name: Set the name of a frame
    - add_element_to_frame: Add an element to a frame
    - remove_element_from_frame: Remove an element from a frame
    - set_element_name: Set the name of an element
    - create_element: Create a new element
    - edit_element: Edit an existing element (content, type, attributes)
    - get_current_canvas_info: Get information about the current canvas
    - set_canvas_name: Set the name of the current canvas
- When asked to show contents of a frame or list of frames, present results by default as a numberedlist, with each item contents summarized to 1-2 sentences.
- When asked to show contents of an element, present results by default as a summarized text.
- These terms are interchangeable:
    - Canvas: space, workspace
    - Frame: group, project, stream, collection
    - Element: message, note, sticker
""",
        tools=[
            fetch_elements,
            create_canvas_frame,
            set_frame_name,
            list_canvas_frames,
            add_element_to_frame,
            remove_element_from_frame,
            set_element_name,
            create_element,
            edit_element,
            get_current_canvas_info,
            set_canvas_name,
        ],
    )

agent = create_agent()
