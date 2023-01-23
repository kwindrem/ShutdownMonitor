/////// new menu for system shutdown

import QtQuick 1.1
import "utils.js" as Utils
import com.victron.velib 1.0

MbPage
{
	id: root
	title: qsTr("System Shutdown")
    VBusItem { id: shutdownItem; bind: Utils.path("com.victronenergy.shutdown", "/Shutdown") }
    VBusItem { id: externalShutdown; bind: Utils.path("com.victronenergy.shutdown", "/ExtShutdownPresent") }
    property bool externalShutdownPresent: externalShutdown.valid && externalShutdown.value == 1

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
            text: qsTr("ShutdownMonitor not running")
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignLeft
            show: !shutdownItem.valid
        }
        MbSwitch
        {
            id: externalShutdownSwitch
            name: qsTr("Enable shutdown pin on Raspberry PI")
            bind: Utils.path("com.victronenergy.settings", "/Settings/ShutdownMonitor/ExternalSwitch")
            writeAccessLevel: User.AccessInstaller
            show: externalShutdownPresent
        }
        MbItemText
        {
            text: qsTr("<b>NOTE:</b> Shutdown pin is GPIO #16 (pin36)\n Take low to shutdown")
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignLeft
            show: externalShutdownPresent
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
