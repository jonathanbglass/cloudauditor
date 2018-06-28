<?php 
include 'common.php';
$title="ISO IAM Auditor - Users";
generate_head($title);
$dbconn = getdb();
$sql = "SELECT * FROM aud_iam_users";
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
print "
<div style=\"overflow-x:auto;\">
  <table>
    <tr>
      <th>AWS<br>Account #</th>
      <th>ARN</th>
      <th>User Name</th>
      <th>User <br> Created</th>
      <th>Password <br> Last Used</th>
    </tr>\n";
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  //print '    <tr><div class="tooltip"><span class="tooltiptext">' . 
   // $resarray[$key]['aud_iam_user_json'] . '</span>' . "\n";
  // iterate over columns
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['arn']  . "</td>\n";
  print '      <td>' . $resarray[$key]['username']  . "</td>\n";
  $thisdate = explode(" ", $resarray[$key]['createdate']);
  print '      <td>' . $thisdate[0] . "</td>\n";
  $thisdate = explode(" ", $resarray[$key]['passwordlastused']);
  print '      <td>' . $thisdate[0] . "</td>\n";
  print "    </tr>\n";
}
print "   </table>
</div>
";
generate_footer();
