<?php

$mysqli = new mysqli("localhost", "pi_user", "skola123", "security_db");

if ($mysqli->connect_errno) {
    echo "Couldn't connect: " . $mysqli->connect_error;
    exit();
}

$pseudo = $_POST['pseudo']; 
$password = $_POST['password'];


$query_str = "SELECT * FROM users WHERE pseudo='$pseudo' AND password='$password'";
$result = $mysqli->query($query_str);

if ($result->num_rows > 0) {
    session_start();
    $row = $result->fetch_assoc(); 
    
    $_SESSION['pseudo'] = $pseudo;
    $_SESSION['role'] = $row['role']; 
    
    
    header("Location: home.php"); 
    exit();
} else {
    echo "Wrong Username or Password!";
}
$mysqli->close();
?>
