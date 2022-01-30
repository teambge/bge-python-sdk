node {
  stage('SCM') {
    checkout scm
  }
  environment {
    JAVA_HOME = '/usr/lib/jvm/jdk-11'
  }
  stage('SonarQube Analysis') {
    def scannerHome = tool 'SonarScanner';
    withSonarQubeEnv() {
      sh "${scannerHome}/bin/sonar-scanner"
    }
  }
}

