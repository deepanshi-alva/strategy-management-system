6/8/25
To show the yellow color in the first column of the row which is being editted until the change is being saved i have made the changes in the update_table_display function in the open_workspace_layout where i have converted the rows to mutable list of lists for editing, then like we have shown the pending rows in the same ways i check if there is any pending edits if yes then based on the row id i make the changes the in the columns. Then afterwards we check if the row has pending edits if yes then make the has_pending_edits boolean field to true and then set the rows whose has_pending_edits is true to yellow color.

Then for setting the color of the particular row only we get the correct row widgets using row_id instead of grid_info. Then after saving the changes we just changed the color back to normal in the auto_save_pending_rows function

7/8/25
changed the configs path to make the auto save common for each and every workspace as it was taking the timer different for different workspaces so just to modify that we just remove the dependency over the workspace id
