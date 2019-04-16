#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
from app.const import Const


class ResultAPI(Const):

    # More types can be created for your specific application needs
    # These items will be in the result record and backend database

    TESTITEM_TIMEOUT = 10.0  # default test item timeout in seconds

    RECORD_RESULT_UNKNOWN = "UNKNOWN" # this is an error if not changed
    RECORD_RESULT_PASS = "PASS"
    RECORD_RESULT_FAIL = "FAIL"
    RECORD_RESULT_TIMEOUT = "TIMEOUT"
    RECORD_RESULT_INCOMPLETE = "INC"
    RECORD_RESULT_INTERNAL_ERROR = "INTERNAL_ERROR"
    RECORD_RESULT_SKIP = "SKIP"
    RECORD_RESULT_DISABLED = "DISABLED"

    UNIT_OHMS = "Ohms"
    UNIT_DB = "dB"
    UNIT_VOLTS = "Volts"
    UNIT_CURRENT = "Amps"
    UNIT_STRING = "STR"
    UNIT_INT = "Integer"
    UNIT_FLOAT = "Float"
    UNIT_CELCIUS = "Celcius"
    UNIT_BOOLEAN = "Boolean"
    UNIT_NONE = None
    UNIT_ALL = [UNIT_OHMS, UNIT_BOOLEAN, UNIT_NONE, UNIT_STRING, UNIT_VOLTS, UNIT_CELCIUS, UNIT_CURRENT,
                UNIT_DB, UNIT_FLOAT, UNIT_INT]


    # ===================================================================================
    # BLOB data types
    #
    # BLOB_UNKNOWN
    # - unknown type of blob
    # - Lente will not try and plot/analyse blobs of this type, they are unknown
    BLOB_UNKNOWN = {
        "type": "BLOB_UNKNOWN",
        "data": None,              # replace with your data, must be JSON serializable
    }

    # Blobs that can be plotted
    # - Lente can plot blob data given the blob data type
    # - blobs that can be plotted, use BLOB_BOKEH_* dicts to define the plot
    # - there are a billion options to plotting with Bokeh, Lente only does bare minimum
    BLOB_BOKEH_FIGURE = {
        "title": "Title",
        "x_axis_type": "auto",  # auto, linear, log, datetime, mercator
        "x_axis_label": "X-Axis",
        "y_axis_type": "auto",  # auto, linear, log, datetime, mercator
        "y_axis_label": "Y-Axis",
    }

    # BLOB_PLOTXY
    # - XY plots
    # - 1 or more lines can be plotted
    # - use this type for plotting waves that fit a template (for example)
    BLOB_PLOTXY_PLOT = {
        "legend": None,  # change to string
        "line_width": 1,
        "x": [],         # x/y list lengths must be the same
        "y": [],
    }
    BLOB_PLOTXY = {
        "type": "BLOB_DICTXY",
        "BLOB_BOKEH_FIGURE": BLOB_BOKEH_FIGURE,
        "plots": [],   # append BLOB_DICTXY_PLOTs here as required...
    }

    # add any new types created here for the purposes of validating
    BLOB_TYPES = [BLOB_UNKNOWN["type"], BLOB_PLOTXY["type"]]

    # TODO: add histogram plot next
