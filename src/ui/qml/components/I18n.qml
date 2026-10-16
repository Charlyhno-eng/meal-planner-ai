pragma Singleton
import QtQuick

QtObject {
    property var translator: null
    readonly property string language: translator ? translator.language : "en"
    function tr(text) {
        // Reading language makes all calling QML bindings reactive to a switch.
        if (language === "en" && translator)
            return translator.translate(text);
        return text;
    }
}
