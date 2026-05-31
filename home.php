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
    <style>
        .center-box { max-width: 500px; margin: 50px auto; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
        .status-btn { display: inline-block; width: 100%; background-color: #2196F3; color: white; padding: 12px; margin: 20px 0 10px 0; font-size: 18px; border-radius: 4px; text-decoration: none; font-weight: bold; }
        .status-btn:hover { background-color: #0b7dda; }
        .admin-btn { display: inline-block; width: 100%; background-color: #9c27b0; color: white; padding: 12px; margin: 5px 0 15px 0; font-size: 18px; border-radius: 4px; text-decoration: none; font-weight: bold; }
        .admin-btn:hover { background-color: #7b1fa2; }
        .logout-btn { display: inline-block; width: 100%; background-color: #f44336; color: white; padding: 10px; font-size: 16px; border-radius: 4px; text-decoration: none; }
        .logout-btn:hover { background-color: #da190b; }
    </style>
</head>
<body style="background-color: #f4f4f4;">

    <div class="blue_gray_title" style="text-align: center; padding: 20px;">
        <h2>Home</h2>
    </div>

    <div class="w3-container">
        <div class="center-box w3-animate-zoom">
            <h2>Welcome</h2>
            <p style="font-size: 18px; margin-top: 15px;">
                Logged in as: <b class="w3-text-blue"><?php echo $_SESSION['pseudo']; ?></b> 
                (<i style="font-size: 14px;"><?php echo $_SESSION['role']; ?></i>)
            </p>
            
            <p style="color: #666;">Click below for controlpanel and real time updates</p>
            
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
