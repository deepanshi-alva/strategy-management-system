[ ui_login.py ] --> Authenticates --> [ db_handler.py ] --> [ users.db ]
                        |
                        v
                [ ui_workspace.py ] --> Shows workspace cards
                        |
                        v
              [ ui_workspace_view.py ]
                 |         |       |
             [Add Row]  [Export]  [Apply]
                 |                   |
     [ instrument_pop.py ]        [ tcp_utils.py ]