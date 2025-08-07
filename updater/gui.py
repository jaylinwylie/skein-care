import webbrowser
import wx
import requests
import updater
from updater.update import check_for_updates


def check_for_updates_dialog(parent_window, defaults: dict = None):
    """
    Check for updates and show a dialog with options to download, skip, or ignore the update.
    
    Args:
        parent_window: The parent window for the dialog
        show_updated: Whether to show a message when no update is available
        defaults: A dictionary that may contain a 'skip_version' key to store skipped versions
        
    Returns:
        True if an update was found, False otherwise
    """
    try:
        # Get the skip_version from defaults if available
        skip_version = None
        if defaults is not None and 'skip_version' in defaults:
            skip_version = defaults.get('skip_version')
            
        # Check for updates, passing the skip_version
        update_info = check_for_updates(skip_version)

        if update_info:
            latest_tag = update_info['tag_name']
            body = update_info['body']
            
            # Create a custom dialog with Skip Version button
            dialog = wx.Dialog(parent_window, title="Update Available", size=(300, 150))
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Message text
            message = wx.StaticText(dialog, label=f"A new update is available!\n{updater.VERSION} -> {latest_tag}\n\n{body}")
            sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)
            
            # Buttons
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # Only add Skip Version button if defaults is provided
            if defaults is not None:
                skip_button = wx.Button(dialog, label="Skip Version")
                
                def on_skip(event):
                    # Add this version to the skip list
                    defaults['skip_version'] = latest_tag
                    dialog.EndModal(wx.ID_CANCEL)
                
                skip_button.Bind(wx.EVT_BUTTON, on_skip)
                button_sizer.Add(skip_button, 0, wx.ALL, 5)
            
            ignore_button = wx.Button(dialog, label="Close")
            release_button = wx.Button(dialog, label="Update")
            
            def on_ignore(event):
                # Just close the dialog
                dialog.EndModal(wx.ID_CANCEL)
            
            def on_release(event):
                webbrowser.open(updater.KO_FI_URL)
                dialog.EndModal(wx.ID_CANCEL)
            
            ignore_button.Bind(wx.EVT_BUTTON, on_ignore)
            release_button.Bind(wx.EVT_BUTTON, on_release)
            
            button_sizer.Add(ignore_button, 0, wx.ALL, 5)
            button_sizer.Add(release_button, 0, wx.ALL, 5)
            sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
            
            dialog.SetSizer(sizer)
            dialog.Fit()
            dialog.ShowModal()
            dialog.Destroy()
            
            return True
        else:
            if not defaults:
                with wx.MessageDialog(parent_window, f"You have the latest version installed.", "Up to Date", wx.OK | wx.ICON_INFORMATION) as dialog:
                    dialog.ShowModal()
            return False

    except requests.exceptions.ConnectionError:
        error_message = f"Failed to query github, No network connection."
        if not defaults:
            with wx.MessageDialog(parent_window, error_message, "Connection error", wx.OK | wx.ICON_INFORMATION) as dialog:
                dialog.ShowModal()
        return False

    except Exception as e:
        error_message = f"Error checking for updates: {str(e)}"
        with wx.MessageDialog(parent_window, error_message, "Update Error", wx.OK | wx.ICON_ERROR) as dialog:
            dialog.ShowModal()
        return False
