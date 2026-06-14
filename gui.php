<?php
session_start();
if (empty($_SESSION['pseudo'])) {
    header("Location: menu.php");
    exit();
}

//session variables to javascript
$loggedInUser = $_SESSION['pseudo'];
$loggedInRole = $_SESSION['role'];
?>
<!DOCTYPE html>
<html>
<head>
    <title>Security System - Panel</title>
    <link rel="stylesheet" href="mystyle.css">
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>
</head>
<body>
    <div id="connectionStatus" class="w3-container w3-green w3-center" style="padding: 5px; margin-bottom: 10px; font-weight: bold; border-radius: 5px;">
        Connected to Raspberry Pi (System Online)
    </div>
    <div class="w3-container container">
        <p>Logged in as: <b><?php echo $loggedInUser; ?></b> (<i><?php echo $loggedInRole; ?></i>)</p>
        <a href="home.php" class="w3-button w3-red w3-round">Back to home</a>
    </div>

    <div id="alarmAlert" class="alarm-trigger-box hidden">
        Larm turned on
    </div>

    <div>
        <div class="w3-container container w3-center">
            <h4>Time left to disarm:</h4>
            <div id="countdownText" class="countdown-badge">-</div>
        </div>

        <div class="w3-container container">
            <h3>Log </h3>
            <div id="adminOwnerBox" class="log-box hidden" > <b>Larm armed by:</b> <span id="alarmOwnerText">-</span></div>
            <div class="log-box"> <b>Larm armed at:</b> <span id="timeArmed">-</span></div>
            <div class="log-box" > <b>Movement detected at:</b> <span id="timeMotion">-</span></div>
            <div class="log-box" > <b>Larm dissarmed at:</b> <span id="timeDisarmed">-</span></div>
        </div>
    </div>

    <script>
        //passes pseudo and role
        var currentUser = "<?php echo $loggedInUser; ?>";
        var currentRole = "<?php echo $loggedInRole; ?>";
        var alarmStartedBy = ""; //keeps the pseudo that set the alarm

        //grants full access on the log
        function hasAccess() {
            
            if (currentRole === "admin") {
                return true;
            }
            //checks if system is idle or client maatches session
            return (alarmStartedBy === "" || currentUser === alarmStartedBy);
        }

        //connection pipelines to HiveMQ over WebSOcket port 8000
        var client = new Paho.MQTT.Client("broker.hivemq.com", 8000, "web_client_" + Math.random());

        //fires instantly whenever any message packet drops down from cloud broker
        client.onMessageArrived = function(message) {
            var topic = message.destinationName; //extracts the path topic
            var val = message.payloadString; //extracts the raw message data from incoming packets
            
            //checks connection status from the Raspberry Pi
            if (topic === "security/heartbeat") { //topic
                var connBox = document.getElementById("connectionStatus");
                if (val === "Online") { //green meaning connected
                    connBox.innerHTML = "Connected to Raspberry Pi (System Online)";
                    connBox.className = "w3-container w3-green w3-center";
                } else { //red meaning no connection
                    connBox.innerHTML = "NOTIFICATION: Connection to Raspberry Pi Lost (System Offline)";
                    connBox.className = "w3-container w3-red w3-center";
                }
                return;
            }

            //evalueates state changes
            if (topic === "security/status") {
                if (val.startsWith("Larm by ")) {
                    alarmStartedBy = val.replace("Larm by ", ""); //isolate the pseudo
                    
                    /*
                    if role is admin it exposes the hidden data box
                    row on screen, which is who set the alarm. 
                    */
                    if (currentRole === "admin") {
                        document.getElementById("alarmOwnerText").innerHTML = alarmStartedBy;
                        document.getElementById("adminOwnerBox").classList.remove("hidden");
                    }
                    document.getElementById("alarmAlert").classList.add("hidden"); 
                }
                /*
                before projecting that the larm has started it checks who 
                has access, the admin has access or the user that matches the session.
                check line 55
                */
                if (val === "LARM STARTED!" && hasAccess()) {
                    //show active alert box
                    document.getElementById("alarmAlert").classList.remove("hidden");
                }

                //flush old parameters once system transitions to seure state
                if (val.includes("Restored") || val === "Secured" || val.includes("Disarmed")) {
                    document.getElementById("alarmAlert").classList.add("hidden");
                    document.getElementById("adminOwnerBox").classList.add("hidden");
                    alarmStartedBy = ""; 
                }
                return;
            } 
            
            /*
            validates user permsission before routing real-time MQTT
            payload (countdown, timestamps) into the log fields
            */
            
            if (hasAccess()) {
                if (topic === "security/countdown") {
                    document.getElementById("countdownText").innerHTML = val + "s";
                    if(val === "0") document.getElementById("countdownText").innerHTML = "-";
                } 
                else if (topic === "security/time_armed") {
                    document.getElementById("timeArmed").innerHTML = val;
                    document.getElementById("timeMotion").innerHTML = "-"; // empty
                    document.getElementById("timeDisarmed").innerHTML = "-";
                } 
                else if (topic === "security/time_motion") {
                    document.getElementById("timeMotion").innerHTML = val;
                } 
                else if (topic === "security/time_disarmed") {
                    document.getElementById("timeDisarmed").innerHTML = val;
                }
            }
        };
        //asynchronous socket hookup routine
        client.connect({onSuccess: function() {
            console.log("Ansluten till MQTT Broker");
            //directs HiveMQ to route all traffic beginning with "security" 
            //down into this web window execution path
            client.subscribe("security/#"); 
        }});
    </script>
</body>
</html>
