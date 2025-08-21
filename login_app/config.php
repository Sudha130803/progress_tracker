<?php
$host = "localhost"; 
$user = "root";       
$pass = "Arun@2005";  // your MySQL password
$db   = "login_app";  

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
