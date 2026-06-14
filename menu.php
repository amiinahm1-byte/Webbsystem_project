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
</head>
<body style="background-color: #f4f4f4;">

    <div class="blue_gray_title" style="text-align: center; padding: 20px;">
        <h2>Security System</h2>
    </div>

    <div class="w3-container">
        <div class="center-box-menu w3-animate-zoom">
            <h3 class="w3-center" style="margin-bottom: 20px; font-weight: bold;">Logga in</h3>
            
            <?php
            //checks the URL parameters, if successful
            if (!empty($_GET['msg']) && $_GET['msg'] == 'registered') {
                echo "<p class='w3-center' style='color:green; font-weight:bold;'>Konto skapat! Logga in här under.</p>";
            }
            ?>

            <form action="login.php" method="post">
                <label><b>Username (Pseudo)</b></label>
                <input type="text" name="pseudo" required>
                
                <label><b>Password</b></label>
                <input type="password" name="password" required>
                
                <input type="submit" value="Logga in" class="submit-btn-menu">
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
