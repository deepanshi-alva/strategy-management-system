This function builds a dynamic instrument selection UI inside a given tkinter frame, allowing users to:
    First select a symbol (e.g., NIFTY, BANKNIFTY)
    Then choose a corresponding instrument name (e.g., specific strike price or expiry)
Once both selections are made, a callback function is triggered with the selected instrument’s details: (name, symbol, token).

Data Source: 
    Uses config.cached_instruments, a shared global list of tuples: (name, symbol, token)
    Groups instruments by symbol for efficient filtering.

UI Components and Flow: 
Element	            |       Purpose
-----------------------------------------------------------------------------------
symbol_dropdown	    |       Dropdown with all distinct instrument symbols.
name_dropdown	    |       Dropdown populated only after a symbol is selected.
OK Button	        |       Triggers callback with selected instrument.
Cancel Button	    |       Closes the popup and resets reference.

Features: 
    Autocomplete on both dropdowns with debounce filtering (500ms).
    Dropdowns prioritize prefix matches and include partial contains matches.
    Dynamically updates instrument names based on the selected symbol.
    Prevents selection until valid inputs are chosen.
    Sends selected data back using a callback (e.g., handle_add_row()).

Internal State: 
Variable	                               |             Role
------------------------------------------------------------------------------------------------------------------------------
instrument_popup	                       |             Reference to the parent frame containing the UI.
symbol_to_instruments	                   |             Dictionary mapping symbols to lists of instruments.
all_symbols / all_names	                   |             Used for filtering dropdown suggestions.
symbol_filter_job / name_filter_job	       |             Debounced filtering job IDs for autocomplete.