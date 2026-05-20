<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $mysqli = new mysqli("localhost", "pi_user", "jacob0416", "security_db");

    if (!$mysqli->connect_errno) {
        $pseudo = $_POST['pseudo'];
        $password = $_POST['password'];
        $first_name = $_POST['first_name'];
        $last_name = $_POST['last_name'];
        $role = "user"; 

        $query_str = "INSERT INTO users (pseudo, password, first_name, last_name, role) 
                      VALUES ('$pseudo', '$password', '$first_name', '$last_name', '$role')";

        if ($mysqli->query($query_str) === TRUE) {
            $mysqli->close();
            header("Location: menu.php?msg=registered");
            exit();
        }
        $mysqli->close();
    }
}
?>
<!DOCTYPE html>
<html lang="sv">
<head>
    <title>Security System - Register</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="mystyle.css">
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <style>
        .center-box { max-width: 450px; margin: 50px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; margin: 8px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="submit"] { width: 100%; background-color: #008CBA; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
    </style>
</head>
<body style="background-color: #f4f4f4;">

    <div class="blue_gray_title" style="text-align: center; padding: 20px;">
        <h2>Security System</h2>
    </div>

    <div class="w3-container">
        <div class="center-box w3-animate-right">
            <h3 class="w3-center" style="margin-bottom: 20px; font-weight: bold;">Skapa konto</h3>
            
            <form action="register.php" method="post">
                <label><b>Username (Pseudo)</b></label>
                <input type="text" name="pseudo" required>
                
                <label><b>Password</b></label>
                <input type="password" name="password" required>
                
                <label><b>First Name</b></label>
                <input type="text" name="first_name" required>
                
                <label><b>Second Name</b></label>
                <input type="text" name="last_name" required>
                
                <input type="submit" value="Registrera konto">
            </form>
            
            <div class="w3-center" style="margin-top: 20px;">
                <a href="menu.php" class="w3-text-red">Stop and go back</a>
            </div>
        </div>
    </div>

    <div class="footer" style="text-align: center; margin-top: 50px;">
        <p>Copyright Webbsystem Course, 2026</p>
    </div>

</body>
</html>