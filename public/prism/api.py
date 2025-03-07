#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2023
Martin Guthrie

"""


class ResultAPI():

    TESTITEM_TIMEOUT = 10.0  # default test item timeout in seconds
                             # Note this can be overridden for any specific test item,
                             # see Example test item TST008_TextInput


    RECORD_RESULT_UNKNOWN = "UNKNOWN" # this is an error if not changed
    RECORD_RESULT_PASS = "PASS"
    RECORD_RESULT_FAIL = "FAIL"
    RECORD_RESULT_TIMEOUT = "TIMEOUT"
    RECORD_RESULT_INCOMPLETE = "INC"
    RECORD_RESULT_INTERNAL_ERROR = "INTERNAL_ERROR"
    RECORD_RESULT_SKIP = "SKIP"
    RECORD_RESULT_DISABLED = "DISABLED"

    # More unit types can be created for your specific application needs,
    # be sure to update UNIT_ALL list.
    # These items will be in the result record and backend database
    UNIT_OHMS = "Ohms"
    UNIT_KILOOHMS = "KiloOhms"
    UNIT_MILLIOHMS = "milliOhms"
    UNIT_DB = "dB"
    UNIT_DBM = "dBm"
    UNIT_VOLTS = "Volts"
    UNIT_MILLIVOLTS = "milliVolts"
    UNIT_CURRENT = "Amps"
    UNIT_AMPS = "Amps"
    UNIT_MILLIAMPS = "milliAmps"
    UNIT_MICROAMPS = "microAmps"
    UNIT_STRING = "STR"
    UNIT_INT = "Integer"
    UNIT_FLOAT = "Float"
    UNIT_CELSIUS = "Celsius"
    UNIT_KELVIN = "Kelvin"
    UNIT_NEWTON = "Newton"
    UNIT_PASCAL = "Pascal"
    UNIT_KILOPASCAL = "KiloPascal"
    UNIT_BAR = "Bar"
    UNIT_METER = "Meter"
    UNIT_MILLIMETER = "Millimeter"
    UNIT_SECONDS = "Seconds"
    UNIT_MILLISECONDS = "Milliseconds"
    UNIT_MICROSECONDS = "Microseconds"
    UNIT_KILOGRAM = "Kilogram"
    UNIT_MILLIGRAM = "milligram"
    UNIT_GRAM = "gram"
    UNIT_LITRE = "litre"
    UNIT_BOOLEAN = "Boolean"
    UNIT_CANDELA = "candela"
    UNIT_HERTZ = "Hertz"
    UNIT_KILOHERTZ = "KiloHertz"
    UNIT_MEGAHERTZ = "MegaHertz"
    UNIT_HENRY = "Henry"
    UNIT_FARADS = "Farads"
    UNIT_SIEMENS = "Siemens"
    UNIT_DEGREE = "Degree"
    UNIT_RAD = "Rad"
    UNIT_PERCENT = "Percent"
    UNIT_WATTS = "Watts"
    UNIT_NONE = "None"

    # any new units added above need to be included in this list for checking
    UNIT_ALL = [UNIT_OHMS, UNIT_KILOOHMS, UNIT_MILLIOHMS, UNIT_DB, UNIT_DBM, UNIT_VOLTS, UNIT_MILLIVOLTS,
                UNIT_CURRENT, UNIT_AMPS, UNIT_MILLIAMPS, UNIT_MICROAMPS, UNIT_STRING, UNIT_INT, UNIT_FLOAT,
                UNIT_CELSIUS, UNIT_KELVIN, UNIT_NEWTON, UNIT_PASCAL, UNIT_KILOPASCAL, UNIT_BAR, UNIT_METER,
                UNIT_MILLIMETER, UNIT_SECONDS, UNIT_MILLISECONDS, UNIT_MICROSECONDS, UNIT_KILOGRAM,
                UNIT_MILLIGRAM, UNIT_GRAM, UNIT_LITRE, UNIT_BOOLEAN, UNIT_CANDELA, UNIT_HERTZ, UNIT_KILOHERTZ,
                UNIT_MEGAHERTZ, UNIT_HENRY, UNIT_FARADS, UNIT_SIEMENS, UNIT_DEGREE, UNIT_RAD, UNIT_PERCENT, UNIT_WATTS,
                UNIT_NONE]

    # ===================================================================================
    # BLOB data types
    #
    # BLOB_UNKNOWN
    # - general purpose JSON blob
    BLOB_UNKNOWN = {
        "type": "BLOB_UNKNOWN",    # DO NOT CHANGE
        "data": None,              # replace with your data, must be JSON serializable
        # you may add your own additional keys
    }

    # Blobs that can be plotted when Lente feature is implemented
    # - Lente MAY plot blob data given the blob data type (plotting not implemented)
    # - blobs that can be plotted, use BLOB_BOKEH_* dicts to define the plot
    # - there are a billion options to plotting with Bokeh,
    #   Lente only does bare minimum, if the plotting feature is implemented
    BLOB_BOKEH_FIGURE = {
        "type": "BLOB_BOKEH_FIGURE",    # DO NOT CHANGE
        "title": "Title",
        "x_axis_type": "auto",  # auto, linear, log, datetime, mercator
        "x_axis_label": "X-Axis",
        "y_axis_type": "auto",  # auto, linear, log, datetime, mercator
        "y_axis_label": "Y-Axis",
        # you may add your own additional keys
    }
    # BLOB_PLOTXY
    # - XY plots
    # - 1 or more lines can be plotted
    # - use this type for plotting waves that fit a template (for example)
    BLOB_PLOTXY_PLOT = {
        "type": "BLOB_PLOTXY_PLOT",    # DO NOT CHANGE
        "legend": None,  # change to string
        "line_width": 1,
        "x": [],         # x/y list lengths must be the same
        "y": [],
        # you may add your own additional keys
    }
    BLOB_PLOTXY = {
        "type": "BLOB_DICTXY",     # DO NOT CHANGE
        "BLOB_BOKEH_FIGURE": BLOB_BOKEH_FIGURE,
        "plots": [],   # append BLOB_PLOTXY_PLOT here as required...
        # you may add your own additional keys
    }

    # add any new types created here for the purposes of validating
    BLOB_TYPES = [BLOB_UNKNOWN["type"],
                  BLOB_PLOTXY["type"],
                  BLOB_PLOTXY_PLOT["type"],
                  BLOB_BOKEH_FIGURE["type"]]

    # TODO: add histogram plot next
