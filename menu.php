<?php
session_start();
?>
<!DOCTYPE html>
<html lang="sv">
<head>
    <title>Security System - Log In</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="mystyle.css">
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <style>
        .center-box { max-width: 450px; margin: 50px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; margin: 10px 0 20px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="submit"] { width: 100%; background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        input[type="submit"]:hover { background-color: #45a049; }
    </style>
</head>
<body style="background-color: #f4f4f4;">

    <div class="blue_gray_title" style="text-align: center; padding: 20px;">
        <h2>Security System</h2>
    </div>

    <div class="w3-container">
        <div class="center-box w3-animate-zoom">
            <h3 class="w3-center" style="margin-bottom: 20px; font-weight: bold;">Logga in</h3>
            
            <?php
            if (!empty($_GET['msg']) && $_GET['msg'] == 'registered') {
                echo "<p class='w3-center' style='color:green; font-weight:bold;'>Konto skapat! Logga in här under.</p>";
            }
            ?>

            <form action="login.php" method="post">
                <label><b>Username (Pseudo)</b></label>
                <input type="text" name="pseudo" required>
                
                <label><b>Password</b></label>
                <input type="password" name="password" required>
                
                <input type="submit" value="Logga in">
            </form>
            
            <div class="w3-center" style="margin-top: 20px;">
                <a href="register.php" class="w3-text-blue">No account? Register here</a>
            </div>
        </div>
    </div>

    <div class="footer" style="text-align: center; margin-top: 50px;">
        <p>Copyright Webbsystem Course, 2026</p>
    </div>

</body>
</html>
