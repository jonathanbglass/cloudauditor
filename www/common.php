<?php 
session_start();
include 'db.php';

function generate_head($title) 
{
?>
<!DOCTYPE html>
<html lang="en">
<head>
<title><?php print $title;?></title>
<link rel="stylesheet" href="/css/style.css">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<script src="/js/script.js"></script>
</head>
<body>
<?php
}

function generate_footer()
{
?>
<div align=center style="font-style: italic;">
Data Classification: Company Confidential
</div>
</body>
</html>
<?php
}
?>
