<?php
session_start();
if (empty($_SESSION['pseudo'])) {
    header("Location: menu.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="sv">
<head>
    <title>Security System - Home</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="mystyle.css">
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
</head>
<body style="background-color: #f4f4f4;">

    <div class="blue_gray_title" style="text-align: center; padding: 20px;">
        <h2>Home</h2>
    </div>

    <div class="w3-container">
        <div class="center-box-home w3-animate-zoom">
            <h2>Welcome</h2>
            <p style="font-size: 18px; margin-top: 15px;">
                Logged in as: <b class="w3-text-blue"><?php echo $_SESSION['pseudo']; ?></b> 
                (<i style="font-size: 14px;"><?php echo $_SESSION['role']; ?></i>)
            </p>
            
            
            
            <a href="gui.php" class="status-btn w3-card-4">Open Panel</a>

            <?php if ($_SESSION['role'] == 'admin'): ?>
                <a href="handling.php" class="admin-btn w3-card-4">Handling Accounts</a>
            <?php endif; ?>
            
            <hr style="border-top: 1px solid #eee; margin: 30px 0;">
            
            <a href="destroy_session.php" class="logout-btn">Logout</a>
        </div>
    </div>

    <div class="footer" style="text-align: center; margin-top: 50px;">
        <p>Copyright Webbsystem Course, 2026</p>
    </div>

</body>
</html>
