#!/usr/bin/env groovy

node('aamprod-ecr-tf9-slave') {
    properties([
        [
            $class: 'HudsonNotificationProperty',
            endpoints: [[
                event: 'all',
                format: 'JSON',
                loglines: 0,
                protocol: 'HTTP',
                timeout: 30000,
                url: 'https://webhooks.gitter.im/e/953b1e47e601cbf09ff8']]
        ],
        [
            $class: 'GithubProjectProperty',
            displayName: 'TS Auth Lib',
            projectUrlStr: 'https://github.com/artsalliancemedia/thunderstorm-auth-library/'
        ]
    ])

    stage('Checkout') {
        checkout scm
    }

    try {
        stage('Test') {
            // run unit tests
            sh 'docker-compose run python3.4 /bin/bash run_test.sh'
            junit 'results.xml'
            sh 'docker-compose run python3.5 /bin/bash run_test.sh'
            junit 'results.xml'
            sh 'docker-compose run python3.6 /bin/bash run_test.sh'
            junit 'results.xml'
            sh 'docker-compose down'
        }
    } catch (err) {
        junit 'results.xml'
        error 'Thunderstorm Client Staging build failed ${err}'

    }
}
