<?php 
include 'common.php';
$dbconn = getdb();
if (isset($_GET['policyarn'])) {
  $sql = "select policyname, policy_document from audit_users_and_policies where policyarn = '" . $_GET['policyarn'] . "' order by insert_ts desc limit 1";
  $res = pg_query($dbconn, $sql);
  $resarray = pg_fetch_all($res);
  header("Content-type: application/json");
  header("Content-Disposition: attachment; filename=" . $resarray[0]['policyname'] . ".json");
  header("Pragma: no-cache");
  header("Expires: 0");
  print '{ "PolicyName": "' . $resarray[0]['policyname'] . '",';
  print ' "PolicyDocument": ' . $resarray[0]['policy_document'] . '}';
  die();
}
// create an accounts array
$acctssql = "select distinct(aws_account_id), aws_account_name from view_audit_users";
$acctsres = pg_query($dbconn, $acctssql);
$acctsresarray = pg_fetch_all($acctsres);
$accounts = array();
foreach ($acctsresarray as $key=>$val) {
  $accounts[$acctsresarray[$key]['aws_account_id']] =  $acctsresarray[$key]['aws_account_name'];
}

$order_by = "aws_account_id asc";
$arrow = "arrow_drop_up";
$c0value = "col_0_asc";
$c1value = "col_1_asc";
$c2value = "col_2_asc";
$c3value = "col_3_asc";
$c4value = "col_4_asc";
$c5value = "col_5_asc";
$c6value = "col_6_asc";
if (isset($_POST['orderby'])) {
  switch ($_POST['orderby']) {
    case "col_0_asc":
      $arrow = "arrow_drop_up";
      $c1value = "col_0_desc";
      $order_by = "aws_account_name asc";
      break;
    case "col_0_desc":
      $arrow = "arrow_drop_down";
      $c1value = "col_0_asc";
      $order_by = "aws_account_name desc";
      break;
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
      $order_by = "insert_ts asc";
      break;
    case "col_4_desc":
      $arrow = "arrow_drop_down";
      $c4value = "col_4_asc";
      $order_by = "insert_ts desc";
      break;
    case "col_5_asc":
      $arrow = "arrow_drop_up";
      $c4value = "col_5_desc";
      $order_by = "policyname asc";
      break;
    case "col_5_desc":
      $arrow = "arrow_drop_down";
      $c4value = "col_5_asc";
      $order_by = "policyname desc";
      break;
    case "col_6_asc":
      $arrow = "arrow_drop_up";
      $c4value = "col_6_desc";
      $order_by = "policyarn asc";
      break;
    case "col_6_desc":
      $arrow = "arrow_drop_down";
      $c4value = "col_6_asc";
      $order_by = "policyarn desc";
      break;
  }
}
// first page load, need to confirm session filter variables don't exist, and set them to true
if (!isset($_SESSION['filterusers']) or !isset($_SESSION['filterroles']) or !isset($_SESSION['filtergroups'])) {
  $_SESSION['filterusers'] = true;
  $_SESSION['filterroles'] = true;
  $_SESSION['filtergroups'] = true;
}

// Deal with filter submissions
if (isset($_POST['filtersubmit'])) {
  if (isset($_POST['filterusers'])) { $_SESSION['filterusers']= true;} else { $_SESSION['filterusers'] = false;}
  if (isset($_POST['filterroles'])) { $_SESSION['filterroles'] = true;} else { $_SESSION['filterroles'] = false;}
  if (isset($_POST['filtergroups'])) { $_SESSION['filtergroups'] = true;} else { $_SESSION['filtergroups'] = false;}
  if (!isset($_POST['filterusers']) && !isset($_POST['filterroles']) && !isset($_POST['filtergroups'])) {
    $_SESSION['filterusers'] = true;
    $_SESSION['filterroles'] = true;
    $_SESSION['filtergroups'] = true;
  }
}
// setup sql statement beginning
$sql = "SELECT aws_account_name, aws_account_id, arn, username, policyname, policyarn, insert_ts from audit_users_and_policies ";

// Deal with Account Filtering submissions
if (isset($_POST['filteraccount'])) { 
  $_SESSION['filteredaccount'] = $_POST['filteraccount'];
  $_SESSION['acctwhere'] = "WHERE aws_account_id = " . $_POST['filteraccount'] . " ";
  if ($_POST['filteraccount'] == "all") { unset($_SESSION['acctwhere']);}
}
if (isset($_SESSION['acctwhere'])) {
  $sql .= $_SESSION['acctwhere'];
}

if ($_SESSION['filterusers'] && $_SESSION['filterroles'] && $_SESSION['filtergroups']) {
} else {
  // we have a filter unchecked; we need to remove that class of data from the query
  // need to count the number of checked items to know how many "or" to add toquery
  $i=0;
  if (isset($_SESSION['acctwhere'])) { $sql .= "AND (";} else { $sql .= "WHERE ";}
  if ($_SESSION['filterusers']) { $i++; $sql .= "arn like '%:user/%' "; }
  if ($_SESSION['filterroles']) { 
    $i++; 
    if ($i>1) { $sql .= "or arn like '%:role/%'"; } else { 
      $sql .= "arn like '%:role/%' ";  }}
  if ($_SESSION['filtergroups']) { $i++; 
    if ($i>1) { $sql .= "or arn like '%:group/%' "; } else { 
      $sql .= "arn like '%:group/%' "; } }
  if (isset($_SESSION['acctwhere'])) { $sql .= ")";}
}

// end SQL with orderby
$sql .= "order by " . $order_by;
$_SESSION['sql']=$sql;
$res = pg_query($dbconn, $_SESSION['sql']);
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
                    "\"aws_account_name\": " . $resarray[$key]['aws_account_name'] . "," .
                    "\"arn\": " . $resarray[$key]['arn'] . "," .
                    "\"username\": \"" . $resarray[$key]['username'] . "\"," .
                    "\"policyname\": \"" . $resarray[$key]['policyname'] . "\"," .
                    "\"policyarn\": \"" . $resarray[$key]['policyarn'] . "\"," .
                    "\"insert_date\": \"" . $resarray[$key]['insert_ts'] . "\"},";
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
  print "SQL -> " . $_SESSION['sql'] . "\n";
  print "aws_account_name,aws_account_id,arn,user_group_role,userid_groupip_roleid,username,insert_date\n";
  foreach ($resarray as $key=>$val) {
    if (strpos($resarray[$key]['arn'], ':group/') !== false) { $identifier = "group"; }
    if (strpos($resarray[$key]['arn'], ':role/') !== false) { $identifier = "role"; }
    if (strpos($resarray[$key]['arn'], ':user/') !== false) { $identifier = "user"; }
    $line = "\"" . $resarray[$key]['aws_account_name'] . "\",";
    $line .= "\"" . sprintf("%'012d", $resarray[$key]['aws_account_id']) . "\",";
    $line .= "\"" . $identifier . "\",";
    $line .= "\"" . $resarray[$key]['arn'] . "\",";
    $line .= "\"" . $resarray[$key]['username'] . "\",";
    $line .= "\"" . $resarray[$key]['policyname'] . "\",";
    $line .= "\"" . $resarray[$key]['policyarn'] . "\",";
    $line .= "\"" . $resarray[$key]['policyi_document'] . "\",";
    $line .= "\"" . $resarray[$key]['insert_ts'] . "\"\n";
    print $line;
  }
  die();
} 
$title="AWS Accounts User and Permission Audit";
generate_head($title);
$num_rows = pg_num_rows($res);
?>
<p align=center>
<div style="overflow-x:auto;">
  <table>
    <tr>
      <td colspan=2>
        Filter by Account
        <form action="" name="filteracct" method="post">
        <select name="filteraccount" onchange="submitform('filteracct')">
          <option value="all">All</option>
<?php
asort($accounts, SORT_NATURAL | SORT_FLAG_CASE);
foreach ($accounts as $key=>$val){
  if ($_SESSION['filteredaccount'] == $key) {
    print "          <option value=\"" . $key . "\" selected>" . $val . "</option>\n";
  }
  else {
    print "          <option value=\"" . $key . "\">" . $val . "</option>\n";
  }
  }
?>
        </form>
      <td>
        <form action="" name="filterdata" method="post">
          Uncheck the Box to Filter Out that Data Type | <br />
          Users <input type="checkbox" name="filterusers" value="users" <?php if ($_SESSION['filterusers']) { print "checked";}?> > |
          Roles <input type="checkbox" name="filterroles" value="roles" <?php if ($_SESSION['filterroles']) { print "checked";}?> > |
          Groups <input type="checkbox" name="filtergroups" value="groups" <?php if ($_SESSION['filtergroups']) { print "checked";}?> > 
          <input type="submit" name="filtersubmit">
        </form>
      </td>
      <td colspan=5 align=center style="font-size:12px;vertical-align:middle;"><?php print $num_rows;?> Rows
        <a href="<?php print $_SERVER['PHP_SELF'];?>?output=csv"><i>Download As CSV</i><i class="material-icons" style="font-size:12px;color:blue;vertical-align:middle;">file_download</i></a>
      </td>
    <tr valign=bottom>

      <th onclick="submitform('postdata0')">
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_0_desc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
  if ($_POST['orderby'] == 'col_0_asc') { print "          <i class=\"material-icons\">$arrow</i>\n"; } } ?>
        <form action="" name="postdata0" method="post">
        AWS<br> Account Name 
          <input type="hidden" name="orderby" value="<?php print $c0value;?>"/>
        </form>
      </th>

      <th onclick="submitform('postdata1')">
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_1_desc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
  if ($_POST['orderby'] == 'col_1_asc') { print "          <i class=\"material-icons\">$arrow</i>\n"; } } ?>
        <form action="" name="postdata1" method="post">
        AWS<br> Account # 
          <input type="hidden" name="orderby" value="<?php print $c1value;?>"/>
        </form>
      </th>

      <th onclick="submitform('postdata2')">
<?php 
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_2_desc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
  if ($_POST['orderby'] == 'col_2_asc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
} else { print "          <i class=\"material-icons\">arrow_drop_up</i>\n";}?>
        <form action="" name="postdata2" method="post">
        User/Group/Role ARN 
          <input type="hidden" name="orderby" value="<?php print $c2value;?>"/>
        </form>
      </th>

      <th onclick="submitform('postdata3')">
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_3_desc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
  if ($_POST['orderby'] == 'col_3_asc') { print "          <i class=\"material-icons\">$arrow</i>\n"; } } ?>
        <form action="" name="postdata3" method="post">
        User/Group/Role Name 
          <input type="hidden" name="orderby" value="<?php print $c3value;?>"/>
        </form>
      </th>

      <th onclick="submitform('postdata5')">
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_5_desc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
  if ($_POST['orderby'] == 'col_5_asc') { print "          <i class=\"material-icons\">$arrow</i>\n"; } } ?>
        <form action="" name="postdata5" method="post">
        Policy Name (link goes to Policy JSON Document) 
          <input type="hidden" name="orderby" value="<?php print $c5value;?>"/>
        </form>
      </th>
      <th onclick="submitform('postdata4')">
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_4_desc') { print "          <i class=\"material-icons\">$arrow</i>\n"; }
  if ($_POST['orderby'] == 'col_4_asc') { print "          <i class=\"material-icons\">$arrow</i>\n"; } } ?>
        <form action="" name="postdata4" method="post">
        Audit Last Recorded Date
          <input type="hidden" name="orderby" value="<?php print $c4value;?>"/>
        </form>
      </th>
    </tr>
<?php
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  print '      <td>' . $resarray[$key]['aws_account_name']  . "</td>\n";
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['arn']  . "</td>\n";
  print '      <td>' . $resarray[$key]['username']  . "</td>\n";
?>         <td>
            <a href="<?php print $_SERVER['PHP_SELF'];?>?policyarn=<?php print $resarray[$key]['policyarn']; ?>">
            <?php print $resarray[$key]['policyname'];?></a>
      </td>
<?php
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
