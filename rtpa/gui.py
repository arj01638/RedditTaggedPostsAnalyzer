import sys
import os
import dearpygui.dearpygui as dpg
import matplotlib
from rtpa.analysis import analyze
from rtpa.exceptions import InsufficientData
from rtpa.graphing.generation import (
    generate_duration_bar_graph, generate_tag_count_bar_graph, generate_script_length_bar_graph,
    generate_subreddit_bar_graph, generate_hourly_bar_graph, generate_hour_block_bar_graph,
    generate_day_bar_graph, generate_common_tag_bar_graph, get_top_and_worst_tags,
    generate_top_and_worst_tags_graph, generate_hour_bar_graph_for_each_day_of_week
)
from rtpa.scraping.old_reddit import scrape as scrape_old_reddit
from rtpa.loader import load_df

class GuiOutputStream:
    def __init__(self):
        self.contents = ""

    def write(self, message):
        self.contents += message
        dpg.set_value("console_output", self.contents)

    def clear(self):
        dpg.set_value("console_output", "")
        self.contents = ""

    def flush(self):
        pass

gos = GuiOutputStream()

def clear():
    gos.clear()

def percentage_string_to_number(percentage_string):
    return float(percentage_string.strip('%')) / 100

def get_input_fields():
    inputs = {}
    inputs['file'] = dpg.get_value("file_input")
    inputs['subreddit'] = dpg.get_value("subreddit_input")
    inputs['filter_tag'] = dpg.get_value("filter_tag_input")
    inputs['confidence_level'] = percentage_string_to_number(dpg.get_value("confidence_level_input"))
    try:
        inputs['n_common_tags'] = int(dpg.get_value("n_common_tags_input")) if dpg.get_value("n_common_tags_input") != "" else 10
    except Exception:
        print("Please enter a valid integer for N Common Tags.")
        return
    try:
        inputs['n_best_worst_tags'] = int(dpg.get_value("n_best_worst_tags_input")) if dpg.get_value("n_best_worst_tags_input") != "" else 10
    except Exception:
        print("Please enter a valid integer for N Best/Worst Tags.")
        return
    try:
        inputs['hour_block'] = int(dpg.get_value("hour_block_input")) if dpg.get_value("hour_block_input") != "" else 3
    except Exception:
        print("Please enter a valid integer for Hour Block.")
        return
    try:
        inputs['minute_block'] = int(dpg.get_value("minute_block_input")) if dpg.get_value("minute_block_input") != "" else 3
    except Exception:
        print("Please enter a valid integer for Minute Block.")
        return
    inputs['graph_style'] = dpg.get_value("graph_style_dropdown")
    inputs['analysis_type'] = dpg.get_value("analysis_type_dropdown")
    inputs['analysis_type_value'] = dpg.get_value("analysis_type_value_input")
    inputs['analysis_metric'] = dpg.get_value("analysis_metric_dropdown")
    inputs['user_subreddit'] = dpg.get_value("user_subreddit_dropdown")
    inputs['user_subreddit_value'] = dpg.get_value("user_subreddit_value_input")
    inputs['time_frame'] = dpg.get_value("time_frame_dropdown")
    inputs['time_input'] = dpg.get_value("time_input")
    inputs['normalize_subreddits'] = dpg.get_value("normalize_subreddits") == "Yes"
    inputs['normalize_inflation'] = dpg.get_value("normalize_inflation") == "Yes"
    return inputs

def generate_graphs_callback(sender, app_data, user_data):
    clear()
    inputs = get_input_fields()
    if inputs is None:
        return
    file = inputs['file']
    subreddit = inputs['subreddit']
    filter_tag = inputs['filter_tag']
    confidence_level = inputs['confidence_level']
    n_common_tags = inputs['n_common_tags']
    n_best_worst_tags = inputs['n_best_worst_tags']
    hour_block = inputs['hour_block']
    minute_block = inputs['minute_block']
    df = get_df()
    if df is None:
        return
    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    directory = "/" + " ".join([file.replace(".csv", "") for file in file.split(',')])
    if subreddit != "":
        directory += f"_{subreddit}"
    if filter_tag != "":
        directory += f"_{filter_tag}"
    time_input = inputs['time_input']
    if time_input is not None:
        directory += f"_{time_input}"
    print(f"Generating graphs in /graphs{directory}/")
    try:
        newline = "\nand "
        print(f"Generated {generate_subreddit_bar_graph(df, confidence_level, directory)}")
        print(f"Generated {generate_hourly_bar_graph(df, confidence_level, subreddit, directory)}")
        print(f"Generated {generate_hour_block_bar_graph(df, confidence_level, subreddit, hour_block, directory)}")
        print(f"Generated {generate_day_bar_graph(df, confidence_level, subreddit, directory)}")
        print(f"Generated {generate_common_tag_bar_graph(df, confidence_level, subreddit, n_common_tags, directory)}")
        best_tags, worst_tags = get_top_and_worst_tags(df, 'Upvotes', confidence_level, n_best_worst_tags)
        out1, out2 = generate_top_and_worst_tags_graph(best_tags, worst_tags, confidence_level, subreddit, directory)
        print(f"Generated {out1 + newline + out2}")
        print(f"Generated {generate_duration_bar_graph(df, confidence_level, subreddit, minute_block, directory)}")
        print(f"Generated {generate_script_length_bar_graph(df, confidence_level, subreddit, 100, directory)}")
        print(f"Generated {generate_tag_count_bar_graph(df, confidence_level, subreddit, directory)}")
        print(f"Generated {generate_hour_bar_graph_for_each_day_of_week(df, confidence_level, subreddit, directory)}")
    except Exception as e:
        print(f"An error occurred:\n {e}")
    print("Done generating graphs. Check the /graphs/ directory.")

def generate_analysis_callback(sender, app_data, user_data):
    clear()
    print("Performing analysis...")
    inputs = get_input_fields()
    if inputs is None:
        return
    analysis_type = inputs['analysis_type']
    analysis_value = inputs['analysis_type_value']
    analysis_metric = inputs['analysis_metric']
    confidence_level = inputs['confidence_level']
    df = get_df()
    if df is None:
        return
    try:
        dpg.set_value("console_output",
                      str(analyze()))
    except Exception as e:
        print(f"An error occurred:\n {e}")

def get_df():
    inputs = get_input_fields()
    if inputs is None:
        return
    file = inputs['file']
    if file == "":
        print("Please enter a value for File(s).")
        return
    subreddit = inputs['subreddit']
    filter_tag = inputs['filter_tag']
    filter_tags = filter_tag.split(',') if filter_tag else []
    time_input = inputs['time_input']
    if time_input == "8yr":
        time_input = 96
    elif time_input == "4yr":
        time_input = 48
    elif time_input == "2yr":
        time_input = 24
    elif time_input == "1yr":
        time_input = 12
    elif time_input == "6m":
        time_input = 6
    elif time_input == "3m":
        time_input = 3
    elif time_input == "1m":
        time_input = 1
    try:
        if ',' in file:
            files = file.split(',')
            df = load_df(files, subreddit, filter_tags, time_input, inputs['normalize_subreddits'], inputs['normalize_inflation'])
        else:
            df = load_df([file], subreddit, filter_tags, time_input, inputs['normalize_subreddits'], inputs['normalize_inflation'])
    except Exception as e:
        print(e)
        return
    return df

def scrape_callback(sender, app_data, user_data):
    clear()
    inputs = get_input_fields()
    if inputs is None:
        return
    user_subreddit = inputs['user_subreddit']
    user_value = inputs['user_subreddit_value']
    time_frame = inputs['time_frame']
    if user_value == "":
        print("Please enter a value for User/Subreddit.")
        return
    if user_subreddit == "user":
        scrape_old_reddit(user_value, None, None)
    elif user_subreddit == "subreddit":
        scrape_old_reddit(None, user_value, time_frame)

def scrape_gwasi_callback(sender, app_data, user_data):
    clear()
    from rtpa.scraping.gwasi import scrape_gwasi
    scrape_gwasi()

def main():
    global gos
    sys.stdout = gos
    dpg.create_context()
    main_window_width = 800
    main_window_height = 800
    window_padding_width = 35
    window_padding_height = 60
    section_width = main_window_width // 2
    spacing_height = 10
    bottom_section_height = main_window_height - 250
    with dpg.window(label="Main Window", no_move=True, no_title_bar=True,
                    width=main_window_width + window_padding_width,
                    height=main_window_height + window_padding_height):
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=section_width - 80)
            dpg.add_text("RTPA", color=(150,150,150), tag="rtpa_text")
            dpg.add_spacer(width=section_width)
        with dpg.font_registry():
            large_font = dpg.add_font(size=72, file="ProggyClean.ttf")
        dpg.bind_item_font("rtpa_text", large_font)
        dpg.add_text("Scraping", color=(255,255,255), tag="scraping_text")
        with dpg.group(horizontal=True):
            with dpg.group(horizontal=True):
                dpg.add_combo(tag="user_subreddit_dropdown", items=["user", "subreddit"],
                              width=section_width//2, default_value="user")
                dpg.add_combo(tag="time_frame_dropdown", items=["all time", "past year", "past month", "past week"],
                              width=section_width//2, default_value="all time")
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="user_subreddit_value_input", width=section_width//2+50)
                dpg.add_button(label="Scrape", callback=scrape_callback, width=section_width//2)
        dpg.add_spacer(height=spacing_height)
        dpg.add_button(label="Scrape GWASI", callback=scrape_gwasi_callback, width=main_window_width+10)
        dpg.add_spacer(height=spacing_height)
        dpg.add_text("Data Loading/Filtering", color=(255,255,255), tag="data_text")
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text("File(s) (comma-separated)")
                dpg.add_input_text(tag="file_input", width=section_width)
            with dpg.group():
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text("Confidence Level")
                        dpg.add_combo(tag="confidence_level_input", items=["90%", "95%", "99%"],
                                      width=section_width//2-4, default_value="95%")
                    with dpg.group():
                        dpg.add_text("Time Cut-off")
                        dpg.add_combo(tag="time_input", items=["8yr","4yr","2yr","1yr","6m","3m","1m"],
                                      width=section_width//2-4, default_value="2yr")
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text("Subreddit")
                dpg.add_input_text(tag="subreddit_input", width=section_width)
            with dpg.group():
                dpg.add_text("Filter Tag(s)")
                dpg.add_input_text(tag="filter_tag_input", width=section_width)
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text("Adj Upvotes by Subreddit")
                dpg.add_combo(tag="normalize_subreddits", items=["No","Yes"], width=section_width//2-4, default_value="No")
            with dpg.group():
                dpg.add_text("Adj Upvotes for Inflation")
                dpg.add_combo(tag="normalize_inflation", items=["No","Yes"], width=section_width//2-4, default_value="No")
        dpg.add_spacer(height=spacing_height*1.5)
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text("Analysis", color=(255,255,255), tag="analysis_text")
                dpg.add_text("Analysis Type")
                dpg.add_combo(tag="analysis_type_dropdown", items=["Tags","Subreddit","Timestamp"], width=section_width, default_value="Tags")
                dpg.add_text("Analysis Value")
                dpg.add_input_text(tag="analysis_type_value_input", width=section_width)
                dpg.add_text("Analysis Metric")
                dpg.add_combo(tag="analysis_metric_dropdown", items=["Upvotes","Comments"], width=section_width, default_value="Upvotes")
                dpg.add_spacer(height=12)
                dpg.add_button(label="Generate Analysis", callback=generate_analysis_callback, width=section_width)
            with dpg.group():
                dpg.add_text("Graphing", color=(255,255,255), tag="graphing_text")
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text("N Common Tags")
                        dpg.add_input_text(tag="n_common_tags_input", width=section_width//2)
                    with dpg.group():
                        dpg.add_text("N Best/Worst Tags")
                        dpg.add_input_text(tag="n_best_worst_tags_input", width=section_width//2-4)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text("Hour Block")
                        dpg.add_input_text(tag="hour_block_input", width=section_width//2)
                    with dpg.group():
                        dpg.add_text("Minute Block")
                        dpg.add_input_text(tag="minute_block_input", width=section_width//2)
                dpg.add_text("Graph Style")
                dpg.add_combo(tag="graph_style_dropdown", items=["Statistical Analysis","Analytics"], width=section_width, default_value="Statistical Analysis")
                dpg.add_spacer(height=12)
                dpg.add_button(label="Generate Graphs", callback=generate_graphs_callback, width=section_width)
        dpg.add_spacer(height=spacing_height)
        with dpg.child_window(label="Console", width=section_width*2+5, height=bottom_section_height, border=True):
            dpg.add_text("Console Output:", tag="console_output", wrap=section_width*2-30)
    dpg.create_viewport(title='Reddit Tagged Posts Analyzer', width=main_window_width+window_padding_width, height=main_window_height+int(1.6*window_padding_height))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    matplotlib.use('agg')
    main()
