6/8/25
To show the yellow color in the first column of the row which is being editted until the change is being saved i have made the changes in the update_table_display function in the open_workspace_layout where i have converted the rows to mutable list of lists for editing, then like we have shown the pending rows in the same ways i check if there is any pending edits if yes then based on the row id i make the changes the in the columns. Then afterwards we check if the row has pending edits if yes then make the has_pending_edits boolean field to true and then set the rows whose has_pending_edits is true to yellow color.

Then for setting the color of the particular row only we get the correct row widgets using row_id instead of grid_info. Then after saving the changes we just changed the color back to normal in the auto_save_pending_rows function

-------------------------------------------------------------------------------------------------

7/8/25
changed the configs path to make the auto save common for each and every workspace as it was taking the timer different for different workspaces so just to modify that we just remove the dependency over the workspace id.

made a variable table_ui_memory and saved the table in that, then made the changes in the auto_save_pending_rows and then in that we made the changes in case an edit is being made in the row so to update that editted text we iterate and make that change in the particular row id

still right now multiple workspaces might not be tackled at the same time i have to look into this issue for a single workspace everything is working fine

-------------------------------------------------------------------------------------------------

8/8/25
today i made the modification to store all the data after reading from the ui to implement this i declared the global variables global_auto_save_job_id, global_auto_save_active_workspaces, and master_window_ref initially they are empty or none

then i made a new function named global_auto_save_all_workspaces where we are saving all the opened workspaces then we store the reference globally so that we can access in auto-save
then we register the workspace for global auto save.

then save the workspace specific pending edits then clear the workspace specific memory all this is happening in the on_close function

then in the update_table_display we have applied the workspace specific pending edits to the edits made in the row irrespective of whether they have saved the data or not we must show the updated things in the ui

then we have made the certain change in the ui for the edit thing where yellow color is being shown in the bg of the checkbox to show that something is being edited in this row  

-------------------------------------------------------------------------------------------------

11/8/25
today i have tested multiple scenerios like took large number of table enteries in a particulat table and then made changes in the rows of that table then i spotted some bugs while testing like multiple workspace data was not being detected its been working for the first workspace opened only so to combat this scenerio we have made the global saving and timer thing

changes the function update_pending_count and then removed the function auto_save_all_tables and made the all the logic shift in the new function made previously that is global_auto_save_all_workspaces

now the only issue which i am seeing still presist in the system is that if we have multiple tables in the workspace the table which are opened only those table data is being there in the storage so the once whose ui is not opened yet but that table has data that tables data will become null as its i is not open in the storage we have null data for this table and thus according to our algo we will delete the table and then insert the new table which will be empty in this case

