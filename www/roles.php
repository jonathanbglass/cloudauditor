<?php 
include 'common.php';
$title="ISO IAM Auditor - Roles";
generate_head($title);
$dbconn = getdb();
$sql = "SELECT * FROM aud_iam_roles";
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
print "
<div style=\"overflow-x:auto;\">
  <table>
    <tr>
      <th>AWS<br>Account #</th>
      <th>ARN</th>
      <th>Role Name</th>
      <th>Create Date</th>
    </tr>\n";
//      <th>Assume Role Policy Document</th>
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['arn']  . "</td>\n";
  print '      <td>' . $resarray[$key]['rolename']  . "</td>\n";
  $thisdate = explode(" ", $resarray[$key]['createdate']);
  print '      <td>' . $thisdate[0] . "</td>\n";
  print "    </tr>\n";
}
print "   </table>
</div>
";
generate_footer();
