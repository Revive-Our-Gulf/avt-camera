def update_valve(pipeline, enable=True):
    record_valve = pipeline.get_by_name("record_valve")
    record_valve.set_property("drop", enable)