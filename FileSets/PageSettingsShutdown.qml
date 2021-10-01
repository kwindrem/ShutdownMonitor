/////// new menu for system shutdown

import QtQuick 1.1
import "utils.js" as Utils
import com.victron.velib 1.0

MbPage
{
	id: root
	title: qsTr("System Shutdown")
    VBusItem { id: shutdownItem; bind: Utils.path("com.victronenergy.shutdown", "/Shutdown") }

    model: VisualItemModel
    {

        MbItemText
        {
            text: qsTr("<b>NOTE:</b> GX device must be power cycled to restart it after shutting down")
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignLeft
            show: shutdownItem.valid
        }
        MbItemText
        {
            text: qsTr("No shutdown dBus parameter - check ShutdownMonitor service")
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignLeft
            show: !shutdownItem.valid
        }
        MbOK
        {
            id: shutdown
            description: qsTr("Shutdown?")
            writeAccessLevel: User.AccessUser
            onClicked:
            {
                toast.createToast(qsTr("Shutting down..."), 10000, "icon-restart-active")
                if (shutdownItem.valid)
                    shutdownItem.setValue (1)
            }
            show: shutdownItem.valid
        }
    }
}
