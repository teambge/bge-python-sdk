pipeline {
  agent any

  environment {
    JAVA_HOME = '/usr/lib/jvm/jdk-11.0.2'
  }

  stages {
    stage('软件配置管理') {
      steps {
        checkout scm
      }
    }

    stage('代码分析') {
      when {
        branch 'master';
      }

      steps {
        script {
          def scannerHome = tool 'SonarScanner';
          withSonarQubeEnv() {
            sh "${scannerHome}/bin/sonar-scanner -Dsonar.branch.name=master"
          }
        }
      }
    }
  }

  triggers {
    GenericTrigger(
      genericVariables: [
        [key: 'ref', value: '$.ref']
      ],
      causeString: 'Triggered on $ref',
      token: 'bge-python-sdk',
      printContributedVariables: true,
      printPostContent: true,
      silentResponse: false,
      regexpFilterText: '$ref',
      regexpFilterExpression: '^refs/heads/master$'
    )
  }
}

