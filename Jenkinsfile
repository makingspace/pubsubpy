pipeline {
    agent any
    options {
        buildDiscarder(logRotator(numToKeepStr: '3'))
    }
    post {
        always {
            deleteDir()
        }
    }
    stages {
        stage('Test') {
            steps {
                sh """#!/bin/bash
                    export PATH="~/.pyenv/bin:$PATH"
                    eval "\$(pyenv init -)"
                    eval "\$(pyenv virtualenv-init -)"
                    pyenv local 3.6.3 2.7.14 3.4.3
                    tox
                """
            }
        }
    }
}
