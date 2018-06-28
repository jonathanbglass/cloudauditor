<?php 
include 'common.php';
?>
<!DOCTYPE html>
<html>
<head>
<title> ISO Auditor </title>
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
Summary Data Goes Here
<ul>
  <li><a href="overview.php">Overview</a>
  <li><a href="accounts.php">AWS Accounts Report</a>
  <li><a href="users.php">ISO Auditor - IAM User Report</a>
  <li><a href="roles.php">ISO Auditor - IAM Role Report</a>
  <li><a href="groups.php">ISO Auditor - IAM Groups Report</a>
  <li><a href="policies.php">ISO Auditor - IAM Policies Report</a>
  <li><a href="crossaccountroles.php">ISO Auditor - Cross Account Roles</a>
</ul>
<?php generate_footer(); ?>
