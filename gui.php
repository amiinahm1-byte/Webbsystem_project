<?php
session_start();
if (empty($_SESSION['pseudo'])) {
    header("Location: menu.php");
    exit();
}

// Skicka med PHP-sessionsvariablerna till JavaScript
$loggedInUser = $_SESSION['pseudo'];
$loggedInRole = $_SESSION['role'];
?>
<!DOCTYPE html>
<html>
<head>
    <title>Security System - Panel</title>
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>
    <style>
        body { font-family: Arial; padding: 20px; background-color: #f4f4f4; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .log-box { font-size: 18px; padding: 10px; background: #fafafa; border-left: 5px solid #2196F3; margin: 10px 0; }
        .countdown-badge { font-size: 48px; font-weight: bold; color: #f44336; text-align: center; }
        .hidden { display: none; } /* Döljer element helt */
        .alarm-trigger-box { background-color: #f44336; color: white; padding: 15px; border-radius: 10px; font-weight: bold; font-size: 20px; text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div id="connectionStatus" class="w3-container w3-green w3-center" style="padding: 5px; margin-bottom: 10px; font-weight: bold; border-radius: 5px;">
        ● Connected to Raspberry Pi (System Online)
    </div>
    <div class="w3-container container">
        <p>Logged in as: <b><?php echo $loggedInUser; ?></b> (<i><?php echo $loggedInRole; ?></i>)</p>
        <a href="home.php" class="w3-button w3-red w3-round">Back to home</a>
    </div>

    <div id="alarmAlert" class="alarm-trigger-box w3-animate-fading hidden">
        Larm turned on
    </div>

    <div>
        <div class="w3-container container w3-center">
            <h4>Time left to disarm:</h4>
            <div id="countdownText" class="countdown-badge">-</div>
        </div>

        <div class="w3-container container">
            <h3>Log </h3>
            <div id="adminOwnerBox" class="log-box hidden" style="border-left-color: #9c27b0;"> <b>Larm armed by:</b> <span id="alarmOwnerText">-</span></div>
            <div class="log-box"> <b>Larm armed at:</b> <span id="timeArmed">-</span></div>
            <div class="log-box" style="border-left-color: #ffeb3b;"> <b>Movement detected at:</b> <span id="timeMotion">-</span></div>
            <div class="log-box" style="border-left-color: #4CAF50;"> <b>Larm dissarmed at:</b> <span id="timeDisarmed">-</span></div>
        </div>
    </div>

    <script>
        var currentUser = "<?php echo $loggedInUser; ?>";
        var currentRole = "<?php echo $loggedInRole; ?>";
        var alarmStartedBy = ""; 

        // UPPDATERAD BEHÖRIGHETSKONTROLL (Säkrad för Admin)
        function hasAccess() {
            // REGEL: Om du är admin, se ALLTID allt direkt (löser låsningsfelet för admin!)
            if (currentRole === "admin") {
                return true;
            }
            // Vanliga användare ser bara om larmet är inaktivt eller om de själva startade det
            return (alarmStartedBy === "" || currentUser === alarmStartedBy);
        }

        // Anslut till HiveMQ-brokern över WebSockets (Port 8000)
        var client = new Paho.MQTT.Client("broker.hivemq.com", 8000, "web_client_" + Math.random());

        client.onMessageArrived = function(message) {
            var topic = message.destinationName;
            var val = message.payloadString;
            
            // 1. Fånga upp nätverksnotisen (Heartbeat / Last Will)
            if (topic === "security/heartbeat") {
                var connBox = document.getElementById("connectionStatus");
                if (val === "Online") {
                    connBox.innerHTML = "● Connected to Raspberry Pi (System Online)";
                    connBox.className = "w3-container w3-green w3-center";
                } else {
                    connBox.innerHTML = "⚠️ NOTIFICATION: Connection to Raspberry Pi Lost (System Offline)";
                    connBox.className = "w3-container w3-red w3-center w3-animate-fading";
                }
                return;
            }

            // 2. Hantera övergripande larmstatus
            if (topic === "security/status") {
                if (val.startsWith("Larmat av ")) {
                    alarmStartedBy = val.replace("Larmat av ", "");
                    
                    // Om du är admin, skriv ut vem som äger sessionen och visa raden
                    if (currentRole === "admin") {
                        document.getElementById("alarmOwnerText").innerHTML = alarmStartedBy;
                        document.getElementById("adminOwnerBox").classList.remove("hidden");
                    }
                    document.getElementById("alarmAlert").classList.add("hidden"); 
                }

                if (val === "💥 LARM UTALÖST!" && hasAccess()) {
                    document.getElementById("alarmAlert").classList.remove("hidden");
                }

                if (val.includes("Återställt") || val === "Grönt system - Säkert" || val.includes("stoppat")) {
                    document.getElementById("alarmAlert").classList.add("hidden");
                    document.getElementById("adminOwnerBox").classList.add("hidden");
                    alarmStartedBy = ""; 
                }
                return;
            } 
            
            // 3. Uppdatera tidtagningar och loggar baserat på behörighet
            if (hasAccess()) {
                if (topic === "security/countdown") {
                    document.getElementById("countdownText").innerHTML = val + "s";
                    if(val === "0") document.getElementById("countdownText").innerHTML = "-";
                } 
                else if (topic === "security/time_armed") {
                    document.getElementById("timeArmed").innerHTML = val;
                    document.getElementById("timeMotion").innerHTML = "-";
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

        client.connect({onSuccess: function() {
            console.log("Ansluten till MQTT Broker");
            client.subscribe("security/#"); 
        }});
    </script>
</body>
</html>
