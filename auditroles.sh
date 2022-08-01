#!/bin/sh
time awk "/^\[profile/ { print substr(\$2, 1, length(\$2)-1);}" ~/.aws/config| sort -i \
| parallel --lb '
if [[ $(grep -c "{} Stop" run.log) -eq 0 ]]
  then
    echo Profile {} Start | tee -a run.log
    [ ! -d {} ] && mkdir {};
    repdate=$(date +"%Y%m%d-%H%M%S")
    report=policies.csv
    awsgo="aws --region us-east-1 --profile {} iam"
    echo Profile {}: Users | tee -a run.log;
    $awsgo list-users > {}/{}_Users.json;
    for nombre in $(jq -rc  '.Users[].UserName' {}/{}_Users.json);
      do
        $awsgo list-attached-user-policies --user-name ${nombre} > {}/{}_UserPoliciesAttached_${nombre}.json;
        sha=$(sha256sum {}/{}_UserPoliciesAttached_${nombre}.json|cut -f 1 -d " ");
        echo $repdate,User-Policies,{},{}/{}_UserPoliciesAttached_${nombre}.json,${sha} >> ${report};
        for polname in $(jq -rc '.AttachedPolicies[].PolicyName' {}/{}_UserPoliciesAttached_${nombre}.json);
          do
            echo "$awsgo get-user-policy --user-name ${nombre} --policy-name ${polname} > {}/{}_UserPolicy_${nombre}_${polname}.json";
            $awsgo get-user-policy --user-name ${nombre} --policy-name ${polname} > {}/{}_UserPolicy_${nombre}_${polname}.json 2>> debug.log;
          done
      done
    echo Profile {}: Groups | tee -a run.log;
    $awsgo list-groups > {}/{}_Groups.json;
    for nombre in $(jq -rc  '.Groups[].GroupName' {}/{}_Groups.json);
      do
        $awsgo list-attached-group-policies --group-name ${nombre} > {}/{}_GroupPoliciesAttached_${nombre}.json;
        sha=$(sha256sum {}/{}_GroupPoliciesAttached_${nombre}.json|cut -f 1 -d " ");
        echo $repdate,Group-Policies,{},{}/{}_GroupPoliciesAttached_${nombre}.json,${sha} >> ${report};
        for polname in $(jq -rc '.AttachedPolicies[].PolicyName' {}/{}_GroupPoliciesAttached_${nombre}.json);
          do
            $awsgo get-group-policy --group-name ${nombre} --policy-name ${polname} > {}/{}_GroupPolicy_${nombre}_${polname}.json;
          done
      done
    echo Profile {}: Roles | tee -a run.log;
    $awsgo list-roles > {}/{}_Roles.json;
    for nombre in $(jq -rc  '.Roles[].RoleName' {}/{}_Roles.json);
      do
        $awsgo list-attached-role-policies --role-name ${nombre} > {}/{}_RolePoliciesAttached_${nombre}.json;
        $awsgo list-role-policies --role-name ${nombre}> {}/{}_RolePoliciesInline_${nombre}.json;
        sha=$(sha256sum {}/{}_RolePoliciesInline_${nombre}.json|cut -f 1 -d " ");
        echo $repdate,Role-Policies,{},{}/{}_RolePoliciesInline_${nombre}.json,${sha} >> ${report};

      done
    echo Profile {}: Policies | tee -a run.log;
    $awsgo list-policies --only-attached > {}/{}_Policies.json;
    for pArn in $(jq -rc  '.Policies[].Arn' {}/{}_Policies.json);
      do
        outfile=$(echo ${pArn}| cut -d ":" -f 6 | sed s+/+_+g);
        # echo aws --region us-east-1 --profile {} iam get-policy --policy-arn ${pArn}
        $awsgo get-policy --policy-arn ${pArn} > {}/{}_Policy_${outfile}.json;
        polver=$(jq -rc '.Policy.DefaultVersionId' {}/{}_Policy_${outfile}.json);
        $awsgo get-policy-version --policy-arn ${pArn} --version-id ${polver} > {}/{}_PolicyVersion_${outfile}_${polver}.json;
        sha=$(sha256sum {}/{}_PolicyVersion_${outfile}_${polver}.json|cut -f 1 -d " ");
        echo $repdate,Policies,{},{}/{}_PolicyVersion_${outfile}_${polver}.json,${sha} >> ${report};
      done
    echo Profile {} Stop | tee -a run.log;
  else
    echo Profile {} Already Processed;
  fi
      '
