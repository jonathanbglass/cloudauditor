<?php 
function getdb() {
    $conn_string = "host=isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com dbname=isodb user=php_readonly";
      $db = pg_connect($conn_string) or die('connection failed');
      return $db;
}

?>
