<?php
// Database connection
$host = "localhost"; 
$user = "root";       // your MySQL username
$pass = "Arun@2005";  // your MySQL root password
$db   = "login_app";  // your database

$conn = new mysqli($host, $user, $pass, $db);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Get user input (from form)
$email = $_POST['email'];
$password = $_POST['password'];

// Check if user already exists
$sql = "SELECT * FROM users WHERE email = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("s", $email);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    // User exists → check password
    $row = $result->fetch_assoc();
    if ($row['password'] === $password) {
        echo "✅ Login successful! Welcome back " . $email;
    } else {
        echo "❌ Wrong password!";
    }
} else {
    // New user → insert into DB
    $sql = "INSERT INTO users (email, password) VALUES (?, ?)";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ss", $email, $password);
    if ($stmt->execute()) {
        echo "🎉 New account created & logged in successfully!";
    } else {
        echo "Error: " . $stmt->error;
    }
}

$conn->close();
?>


