This is a large python GUI application using Tkinter, built for managing user defined data tables which stores strategies in a trading / analytical system

1) get_next_session_id = think of it like a counter that generates unique number each time. Global_session_counter starts from a number and increases everytime you add a new row.

In this we are using threading for async background operation used when sending TCP commands to avoid freezing the UI.

Then we have the list of action buttons and the variables defining the state of various popups like table action popup, imp_exp_window popup and the system_confiug popup. The action buttons are being used later in the UI setup under open_workspace_layout to auto create the buttons

2) create_validator(data_type) = this dynamically generates a validator function based on column data type. When editing the table value, used when rendering input fields for rows, ensures invalid input is prevented at UI level and if the things goes well at the ui level then we are saving the data after reading from the ui only.

3) open_create_table_popup = this function allows user to define a new table, specify column names, datatypes, default values , editable and subscription flags and save it to the db 
Now it creates popup window anchored to the parent(main window). Type the logical table name.
Holds all column input rows. column_entries : list of (name, dtype, deault, editable, subsription)

    i) add_column() = each column row includes
            a) column name input
            b) select data type from the dropdown
            c) default value
            d) editable checkbox to mark column as default initially
            e) subscription checkbox to mark column as editable after being activated
            f) remove this column button

    ii) remove_column() = deletes the entry from the column enteries and also destroys the row frame

    iii) create_table() = this is called when user presses create table converts the table_name to upper case and if empty shows error.
    Each column is a dictionary so append each dictionary into the schema array. Now create unique sqlite table name. The actual columns include system fields : ID, Strategy, Status etc plus your custom schema. Then create the table and save metadata to user tables.
    Then we have the final cleanup where we close the DB, closes the popup, triggers UI refresh in main workspace so the new table shows up
    
4) open_edit_table_popup = It loads existing schema from DB. Let user modify column name, types, defaults, editable flags, subsription flags etc. Rename table (logical name). Rebuilt physical tables if columns are removed. Allow deleting the table completely
Then we read the existing schema JSON from user_tables for this user+workspace+table. If table not found -> error popup and exit. Then we have the popup window with the same format as the create table window . Prefills current table name in the text box.

    i) add_column_with_values = this helper function populates row using exiting column data. It builts the same ui widgets as in the create flow then loops through schema_data and adds all the existing columns.

    ii) remove_column() = works same as the create table popup remove button where we delete the entry from the column_entries dictionary

    iii) save_changes() = when the user presses save changes the following things happen : if the new name is blank then show error. If name was changes check if new name already exists for this user / workspace 
    Then in new_schema we will append the schema which is being created. Then fetch the old_schema and compare the new schema with it to detect the changes.
    Now if columns are being dropped then recreate table as sqlite cant drop columns. So to achieve this rename the current table to temp, create new table with updated schema, copy common columns from temp to new table, drop the temp table.
    Add new columns (if any) and set default value for all other existing rows for the new column that is being added
    Then finally update the table metadata and do the final cleanup

    iv) delete_table() = it deletes both the physical_table and its metadata and refereshes the ui

5) handle_add_row = in this we receive the user id, workspace id, table name, instrument detials like name, symbol and token. Inside the function we fetch the exiting table schema and the name of the table. Then we will get the next id using the get_next_session_id function, then we will make the next row with the data that we have and add the user defined columns with the defaults. Then we just save that new row and the physical table in the pending rows variable and then it will auto save after some time as we have to build the functionality in such a way that the data is not being saved in the db directly it will be saved after a particular time.

6) open_workspace_layout() = This function opens fullscreen GUI for a workspace. Loads table for the user. Lets you view and manage rows. Providing buttons: add row, apply, stop etc. Handles relatime status updates and tcp strategy commands
In this we fetch internal userId with their email. Load workspace properties and entry_widgets_by_row_id is a central dictionary that stores UI references for each row for dynamic updates.
In this we first load the system configuration for the user so that we get to know the interval in which the user want to save the data.

    i) on_workspace_close() = on close, checks if any row in any tables has stutus = active. If yes -> shows warning and blocks close. If all are inactive -> calls cleanup_window() and also save all the pending rows and the pending edits before closing and the cleanup

then we have the header, dropdown where we can select which table to display and on change in the dropdown we trigger update_table _display() to reload rows
content_frame is where the scrollable data table is rendered dynamically. Eptied and rebuit every time the selected table changes.

Row status update functions ->
    ii) update_row_ui_waiting
    iii) update_row_ui_active
    iv) update_row_ui_inactive
They update background color, field values, button states and checkbox states

    v) handle_start_all / handle_stop_all = These loop through all rows in the current table and send tcp apply_strategy or stop_strategy. On success -> updates the DB + UI. On failure -> show popup + revert UI. They use send_tcp_command(command, callback=...) - the external tcp connector. Callbacks update status + refresh UI

    vi) set_default_table = marked any one table as default in a particular workspace.

    vii) update_table_display() = this is a hige and critical function where we read schema + row data from the selected physical table. Build scrollable TKinter canvas. Adds one row per db row

        a) clear old ui (content frame)
        b) fetch table name -> physical_name
        c) fetch rows
        d) fetch schema
        e) create scrollable canvas 
        f) create headers
        g) for each row : build widgets and attach logic
        h) create action buttons per row
        i) show message if table is empty
        j) update global entry_widgets_by_row_id

expties main table area and resets entry_widgets_by_row_id dictionary that tracks widget references for each row

    viii) update_strategy_status_display() = this function continously shows how many strategies are running. Updates on every major event

    ix) refresh_tables() = after add, delete, import, edit table and also after row add / delete and on initial load this function is being called to refresh the whole ui and show the updated ui with all the addition and the deletions

    x) export_table_as_json() = uses asksaveasfilename to save the currently selected table schema + data. Resets all status to inactive

    xi) export_schema_only() = uses asksaveasfilename to save the currently selected table schema only so that the user dont have to create the table and mention the column details again

    xii) import_table_from_json() = assign new ids and strategies, creates new physical table if needed, inserts into user_tables and row table

    xiii) import_schema_only() = it imports the schema from the selected file and save it into the user_tables as well as create a new physical table with the unique name

    xiv) open_table_actions_popup() = it open the table action popup in which we have a notebook that contains three tabs as of now and we can extent it further as per our requirement. The three tabs that are present currently are : new table, edit table, add row. Each tab has their own functions to be performed. 

    xv) open_import_export_popup() = this opens the popup that contains 4 buttons : improt schema, export schema, import table and export table. Each button has their own functionality. On clicking the export schema will export the schema of the table and vice versa happens in the case of import schema. In case of export table we export the schema along with the data that is present in the table as well and the vice versa happens in the case of import table

    xvi) open_system_configuration_popup() = here the popup will open where for now we have given the user the authority to select the time interval in which they want there data to be saved in the db and if this auto saving feature is turned off then the default timer is 5 min that means after every 5 mins the data will be saved in the db

    xvii) update_pending_count() = this update the count of the pending rows and the pending edits which are yet to be saved in the db

    xviii) update_timer_from_global() = this update the timer from the global_elapsed_seconds in hours:minutes:seconds formal

    xix) auto_save_pending_rows() = in this we are checking whether the elapsed time is greater than the interval in second and if this is true then we trigger the auto saving mode and clear the pending edits and the pending rows dictionary