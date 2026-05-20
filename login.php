<?php
// Anslutningsinfo från din labb [cite: 152]
$mysqli = new mysqli("localhost", "pi_user", "skola123", "security_db");

if ($mysqli->connect_errno) {
    echo "Couldn't connect: " . $mysqli->connect_error;
    exit();
}

$pseudo = $_POST['pseudo']; // Hämtar från formuläret [cite: 187]
$password = $_POST['password'];

// SQL-fråga för att hitta användaren [cite: 185]
$query_str = "SELECT * FROM users WHERE pseudo='$pseudo' AND password='$password'";
$result = $mysqli->query($query_str);

if ($result->num_rows > 0) {
    session_start();
    $row = $result->fetch_assoc(); 
    
    $_SESSION['pseudo'] = $pseudo;
    $_SESSION['role'] = $row['role']; 
    
    // ÄNDRAD RAD: Skicka till hemsidan
    header("Location: home.php"); 
    exit();
} else {
    echo "Wrong Username or Password!";
}
$mysqli->close();
?>