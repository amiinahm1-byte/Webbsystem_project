<?php
//connects to local database
$mysqli = new mysqli("localhost", "pi_user", "skola123", "security_db");
//if error
if ($mysqli->connect_errno) {
    echo "Couldn't connect: " . $mysqli->connect_error;
    exit();
}

//get oseudo and password
$pseudo = $_POST['pseudo']; 
$password = $_POST['password'];

//query for matching rows credentials
$query_str = "SELECT * FROM users WHERE pseudo='$pseudo' AND password='$password'";
$result = $mysqli->query($query_str);//execute quesry inside the MySQL engine


if ($result->num_rows > 0) {
    session_start(); //start session
    $row = $result->fetch_assoc(); 
    
    //creates a secure server session tracking pseudo and role
    $_SESSION['pseudo'] = $pseudo;
    $_SESSION['role'] = $row['role']; 
    
    //sends a raw HTTP header
    header("Location: home.php"); 
    exit();
} else {
    echo "Wrong Username or Password!";
}
$mysqli->close();
?>
