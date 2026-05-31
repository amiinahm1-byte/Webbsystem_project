<?php
session_start();

// Säkerhetsspärr: Endast admin får se denna sida
if (empty($_SESSION['pseudo']) || $_SESSION['role'] !== 'admin') {
    header("Location: home.php");
    exit();
}

$mysqli = new mysqli("localhost", "pi_user", "skola123", "security_db");
$message = "";
$message_color = "red";

// Hantera radering när admin har fyllt i sina bekräftelseuppgifter
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['confirm_delete'])) {
    $admin_pseudo = $_POST['admin_pseudo'];
    $admin_password = $_POST['admin_password'];
    $user_to_delete = $_POST['user_to_delete'];

    // 1. Verifiera att det faktiskt är den riktiga admin som bekräftar med rätt lösenord
    $stmt = $mysqli->prepare("SELECT role FROM users WHERE pseudo = ? AND password = ?");
    $stmt->bind_param("ss", $admin_pseudo, $admin_password);
    $stmt->execute();
    $result = $stmt->get_result();
    $admin_check = $result->fetch_assoc();

    if ($admin_check && $admin_check['role'] === 'admin') {
        // 2. Kontrollen lyckades! Radera användarkontot
        $delete_stmt = $mysqli->prepare("DELETE FROM users WHERE pseudo = ? AND role != 'admin'");
        $delete_stmt->bind_param("s", $user_to_delete);
        if ($delete_stmt->execute()) {
            $message = "Account for '$user_to_delete' was successfully removed.";
            $message_color = "green";
        } else {
            $message = "Error: Could not delete account.";
        }
        $delete_stmt->close();
    } else {
        $message = "Verification failed! Incorrect Admin username or password.";
    }
    $stmt->close();
}
?>
<!DOCTYPE html>
<html lang="sv">
<head>
    <title>Security System - Handling Accounts</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="mystyle.css">
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <style>
        .center-box { max-width: 600px; margin: 50px auto; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .user-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #eee; }
        .remove-btn { background-color: #f44336; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
        .remove-btn:hover { background-color: #d32f2f; }
        .modal-box { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; margin: 8px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; }
    </style>
</head>
<body style="background-color: #f4f4f4;">

    <div class="blue_gray_title" style="text-align: center; padding: 20px;">
        <h2>Handling Accounts</h2>
    </div>

    <div class="w3-container">
        <div class="center-box w3-animate-zoom">
            <h3 style="font-weight: bold; border-bottom: 2px solid #9c27b0; padding-bottom: 10px;">Registered Users</h3>
            
            <?php if (!empty($message)): ?>
                <p style="color: <?php echo $message_color; ?>; font-weight: bold; text-align: center; margin: 15px 0;">
                    <?php echo $message; ?>
                </p>
            <?php endif; ?>

            <div style="margin-top: 20px;">
                <?php
                // Hämta alla användare som inte är admin för att lista dem
                $result = $mysqli->query("SELECT pseudo, first_name, last_name, role FROM users WHERE role != 'admin'");
                
                if ($result->num_rows > 0) {
                    while ($row = $result->fetch_assoc()) {
                        echo "<div class='user-item'>";
                        echo "<div>";
                        echo "<b>" . htmlspecialchars($row['pseudo']) . "</b> - " . htmlspecialchars($row['first_name']) . " " . htmlspecialchars($row['last_name']);
                        echo "</div>";
                        // När man klickar här öppnas modalen (pop-upen) via JavaScript och sätter rätt användarnamn i formuläret
                        echo "<button type='button' class='remove-btn' onclick='openConfirmModal(\"" . htmlspecialchars($row['pseudo']) . "\")'>Remove</button>";
                        echo "</div>";
                    }
                } else {
                    echo "<p style='color: #888; text-align: center;'>No standard user accounts found.</p>";
                }
                ?>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="home.php" class="w3-button w3-gray w3-round">Back to Home</a>
            </div>
        </div>
    </div>

    <div id="confirmModal" class="w3-modal">
        <div class="modal-box w3-animate-top w3-card-4">
            <h3 style="font-weight: bold; color: #f44336;">Confirm Deletion</h3>
            <p>You are about to remove user: <b id="targetUserText" class="w3-text-red"></b></p>
            
            <form action="handling.php" method="post" style="margin-top: 20px;">
                <input type="hidden" id="userToDeleteInput" name="user_to_delete">

                <label><b>Your Admin Username (Pseudo)</b></label>
                <input type="text" name="admin_pseudo" required>

                <label><b>Your Admin Password</b></label>
                <input type="password" name="admin_password" required>

                <input type="submit" name="confirm_delete" value="Confirm and Delete" class="w3-button w3-red w3-round style='width: 100%; margin-top: 10px;'">
                <button type="button" onclick="closeConfirmModal()" class="w3-button w3-gray w3-round" style="width: 100%; margin-top: 10px;">Cancel</button>
            </form>
        </div>
    </div>

    <script>
        function openConfirmModal(username) {
            document.getElementById('targetUserText').innerText = username;
            document.getElementById('userToDeleteInput').value = username;
            document.getElementById('confirmModal').style.display = 'block';
        }

        function closeConfirmModal() {
            document.getElementById('confirmModal').style.display = 'none';
        }
    </script>

    <div class="footer" style="text-align: center; margin-top: 50px;">
        <p>Copyright Webbsystem Course, 2026</p>
    </div>

</body>
</html>
<?php $mysqli->close(); ?>
