import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import QtQml.Models 2.15
import Qt.labs.platform 1.0	
import Qt.labs.settings 1.0
ApplicationWindow {
    visible: true
    title: "FED3"

    property QtObject backend
    property string log_text
    property var options: []

    property int width_: 900
    property int height_: 1200
    width: width_
    height: height_
    maximumHeight: height_
    minimumHeight: height_
    maximumWidth: width_
    minimumWidth: width_

    Settings {
        id: settings
        property string file_url: ""
    }

    Connections { 
        target: backend
        function onLoad() {
            backend.set_file(settings.file_url);
        }

    }
    
    function min(a,b) {
        return a<b ? a : b;
    }

    Rectangle {

        anchors.fill: parent

        ColumnLayout {
            anchors.fill: parent
            width: parent.width 
            height: parent.height
            spacing: 0
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.maximumHeight: Window.height / 15
                RowLayout {
                    width: parent.width
                    height: parent.height
                    layoutDirection: RowLayout.RightToLeft
                    ComboBox {
                        background: Rectangle {
                            implicitWidth: parent.parent.width / 5
                            implicitHeight: parent.parent.height
                            color: 'lightgray'
                            radius: 2
                            
                        }

                        id: myBox
                        model: options

                        onActivated: {
                            backend.set_port(currentIndex);
                        }

                    }
                }
            }


            Rectangle {
                implicitWidth: parent.width;
                implicitHeight: parent.height /2
                Image {
                    anchors.fill: parent;
                    source: 'fed3.png'
                    fillMode: Image.PreserveAspectFit
                }
            }
 
            Rectangle {
                Layout.fillWidth: true
                height: Window.height/15
                RowLayout {
                    anchors.fill: parent
                    spacing: -Window.width / 400
                    Button {
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        implicitWidth: Window.width / 2.2
                        Layout.margins: min(Window.width / 100,10)
                        text: "Syncronize Time"
                        onClicked: {backend.sync()}
                        Component.onCompleted: {background.color = "mediumpurple"}
                    }
                    Button {
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        
                        implicitWidth: Window.width / 2.2
                        Layout.margins: min(Window.width / 100,10)
                        text: "Record"
                        onClicked: {
                            backend.record();
                            text = !backend.recording ? "Record" : "Stop";
                            background.color = !backend.recording ? "lime" : "red";
                        }
                        Component.onCompleted: {background.color = "lime"}
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: Window.height/15
                RowLayout {
                    anchors.fill: parent
                    spacing: -2.5
                    TextField {
                        id: field
                        text: settings.file_url
                        onTextEdited: settings.file_url = text
                        placeholderText: "enter file"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.margins: min(Window.width / 200,10)
                        onEditingFinished : {
                            settings.file_url = text;
                            backend.set_file(text,true);
                        }
                    }

                    Button {
                        text: '...'
                        implicitWidth: parent.height  - Window.width / 50;
                        implicitHeight: parent.height - Window.width / 50;
                        Layout.margins: min(Window.width / 200,10)
                        onClicked: {
                            filedialog.open()
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: Window.height / 5
                Rectangle{
                    width: parent.width -Window.width / 200
                    height: parent.height -Window.width / 200
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    border.color: 'grey'
                    radius: 3
                    Flickable {
                        id: scroll
                        anchors.fill: parent
                        contentWidth: log.contentWidth
                        contentHeight: log.contentHeight
                        clip: true
                        ScrollBar.vertical: ScrollBar {policy: ScrollBar.AlwaysOn}


                        function ensureVisible(r) {
                            if(contentX >= r.x)
                                contentX = r.x;
                            else if (contentX+width <= r.x+r.width)
                                contentX = r.x+r.width - width;
                
                            if(contentY >= r.y)
                                contentY = r.y;
                            else if (contentY+height <= r.y+r.height)
                                contentY = r.y+r.height - height + 10;

                        }
                            
                        function scrollToEnd() {
                            var ratio = 1.0-visibleArea.heightRatio
                            var endPos = contentHeight*(1.0-visibleArea.heightRatio)
                            contentY = contentHeight*(1.0-visibleArea.heightRatio)
                        }


                        TextEdit {
                            id: log

                            font.family: "Monospace"

                            readOnly: true
                            text: log_text
                            padding: Window.width / 100
                            wrapMode: TextEdit.Wrap
                            width: scroll.width
                            onCursorRectangleChanged: {
                                scroll.ensureVisible(cursorRectangle)
                                scroll.scrollToEnd()
                            }
                        }
                    }
                }
            }

            FileDialog {
                id: filedialog
                onAccepted: {
                    var file = String(currentFile).slice(7);
                    field.text = file;
                    settings.file_url = file;
                    backend.set_file(file,false);
                }
                nameFilters: "CSV (*.csv)"
                defaultSuffix: "csv"
                fileMode: FileDialog.SaveFile

            }
        
        }
    }
}