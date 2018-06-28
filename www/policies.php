<?php 
include 'common.php';
$title="ISO IAM Auditor - Policies";
generate_head($title);
$dbconn = getdb();
$sql = "SELECT * FROM aud_iam_policies";
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
print "
<div style=\"overflow-x:auto;\">
  <table>
    <tr>
      <th>AWS Account #</th>
      <th>ARN</th>
      <th>Policy Name</th>
      <th>Attachment<br>Count</th>
      <th>Create Date</th>
      <th>Updated Date</th>
    </tr>\n";
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['aud_iam_policy_arn']  . "</td>\n";
  print '      <td>' . $resarray[$key]['aud_iam_policy_policyname']  . "</td>\n";
  print '      <td>' . $resarray[$key]['aud_iam_policy_attachmentcount']  . "</td>\n";
  $thisdate = explode(" ", $resarray[$key]['aud_iam_policy_createdate']);
  print '      <td>' . $thisdate[0] . "</td>\n";
  $thisdate = explode(" ", $resarray[$key]['aud_iam_policy_updatedate']);
  print '      <td>' . $thisdate[0] . "</td>\n";
  print "    </tr>\n";
}
print "   </table>
</div>
";
generate_footer();
?>
