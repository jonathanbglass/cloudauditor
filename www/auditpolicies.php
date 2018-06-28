<?php 
include 'common.php';
$order_by = "aws_account_id asc";
$dbconn = getdb();
$sql = "SELECT * from view_audit_users order by " . $order_by;
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
# Generate JSON file
if (isset($_GET['output']) && $_GET['output'] == 'json') {
  header("Content-type: application/json");
  header("Content-Disposition: attachment; filename=aws_account_audit.json");
  header("Pragma: no-cache");
  header("Expires: 0");
  $jsonoutput= "[";
  foreach ($resarray as $key=>$val) {
    $jsonoutput .=  "{\"aws_account_id\": " . $resarray[$key]['aws_account_id'] . "," . 
                    "\"arn\": " . $resarray[$key]['arn'] . "," .
                    "\"userid\": \"" . $resarray[$key]['userid'] . "\"," .
                    "\"username\": \"" . $resarray[$key]['username'] . "\"," .
                    "\"insert_date\": \"" . $resarray[$key]['insert_ts'] . "\"," .
                    "\"passwordlastused\": \"" .  $resarray[$key]['passwordlastused'] . "\"},";
  }
  $jsonoutput = substr_replace($jsonoutput, '', -1);
  $jsonoutput .= "]";
  print $jsonoutput;
  die();
}
# Generate CSV file
if (isset($_GET['output']) && $_GET['output'] == 'csv') {
  header("Content-type: text/csv");
  header("Content-Disposition: attachment; filename=aws_account_audit.csv");
  header("Pragma: no-cache");
  header("Expires: 0");
  print "aws_account_id,arn,userid,username,passwordlastused,insert_date\n";
  foreach ($resarray as $key=>$val) {
    $line = "\"" . sprintf("%'012d", $resarray[$key]['aws_account_id']) . "\",";
    $line .= "\"" . $resarray[$key]['arn'] . "\",";
    $line .= "\"" . $resarray[$key]['userid'] . "\",";
    $line .= "\"" . $resarray[$key]['username'] . "\",";
    $line .= "\"" . $resarray[$key]['passwordlastused'] . "\",";
    $line .= "\"" . $resarray[$key]['insert_ts'] . "\"\n";
    print $line;
  }
  die();
} 
$title="AWS Accounts User and Permission Audit";
generate_head($title);
$arrow = "arrow_drop_up";
$c1value = "col_1_asc";
$c2value = "col_2_asc";
$c3value = "col_3_asc";
$c4value = "col_4_asc";
$c5value = "col_5_asc";
if (isset($_POST['orderby'])) {
  switch ($_POST['orderby']) {
    case "col_1_asc":
      $arrow = "arrow_drop_up";
      $c1value = "col_1_desc";
      $order_by = "aws_account_id asc";
      break;
    case "col_1_desc":
      $arrow = "arrow_drop_down";
      $c1value = "col_1_asc";
      $order_by = "aws_account_id desc";
      break;
    case "col_2_asc":
      $arrow = "arrow_drop_up";
      $c2value = "col_2_desc";
      $order_by = "arn asc";
      break;
    case "col_2_desc":
      $arrow = "arrow_drop_down";
      $c2value = "col_2_asc";
      $order_by = "arn desc";
      break;
    case "col_3_asc":
      $arrow = "arrow_drop_up";
      $c3value = "col_3_desc";
      $order_by = "username asc";
      break;
    case "col_3_desc":
      $arrow = "arrow_drop_down";
      $c3value = "col_3_asc";
      $order_by = "username desc";
      break;
    case "col_4_asc":
      $arrow = "arrow_drop_up";
      $c4value = "col_4_desc";
      $order_by = "passwordlastused asc";
      break;
    case "col_4_desc":
      $arrow = "arrow_drop_down";
      $c4value = "col_4_asc";
      $order_by = "passwordlastused desc";
      break;
    case "col_5_asc":
      $arrow = "arrow_drop_up";
      $c5value = "col_5_desc";
      $order_by = "insert_ts asc";
      break;
    case "col_5_desc":
      $arrow = "arrow_drop_down";
      $c5value = "col_5_asc";
      $order_by = "insert_ts desc";
      break;
  }
}
?>
<p align=center>
<div style="overflow-x:auto;">
  <table>
    <tr>
      <td colspan=6 align=right style="font-size:12px;vertical-align:middle;"><a href="<?php print $_SERVER['PHP_SELF'];?>?output=csv"><i>Download As CSV</i><i class="material-icons" style="font-size:12px;color:blue;vertical-align:middle;">file_download</i></a></td>
    <tr valign=bottom>
      <th onclick="submitform('postdata1')">
        AWS<br> Account # 
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_1_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_1_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata1" method="post">
        <input type="hidden" name="orderby" value="<?php print $c1value;?>"/>
        </form></th>
      <th onclick="submitform('postdata2')">
        User ARN 
<?php 
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_2_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_2_asc') { print "<i class=\"material-icons\">$arrow</i>"; }
} else { print "<i class=\"material-icons\">arrow_drop_up</i>";}?>
        <form action="" name="postdata2" method="post">
        <input type="hidden" name="orderby" value="<?php print $c2value;?>"/>
        </form></th>
      <th onclick="submitform('postdata3')">
        User Name 
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_3_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_3_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata3" method="post">
        <input type="hidden" name="orderby" value="<?php print $c3value;?>"/>
        </form></th>
      <th onclick="submitform('postdata4')">
        Password Last Used
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_4_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_4_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata4" method="post">
        <input type="hidden" name="orderby" value="<?php print $c4value;?>"/>
        </form></th>
      <th onclick="submitform('postdata5')">
        Audit Last Recorded Date
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_5_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_5_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata5" method="post">
        <input type="hidden" name="orderby" value="<?php print $c5value;?>"/>
        </form></th>
    </tr>
<?php
$sql = "SELECT * from view_audit_users order by " . $order_by;
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['arn']  . "</td>\n";
  print '      <td>' . $resarray[$key]['username']  . "</td>\n";
  print '      <td>' . $resarray[$key]['passwordlastused']  . "</td>\n";
  print '      <td>' . $resarray[$key]['insert_ts']  . "</td>\n";
  print "    </tr>\n";
}
?>
   </table>
</div>
<div id="footer" align=center>
Data Collected: <?php #print $date_collected ;?>
<p>
Data Classification: Company Confidential
</div>
<div id="chart"></div>
  </body>
  </html>
