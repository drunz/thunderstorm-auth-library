#!/usr/bin/env groovy

node('aam-identity-prodcd') {
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
            // run unit tests, tox runs make test codacy
            // CODACY_PROJECT_TS_AUTH_LIB_TOKEN is a global set in jenkins
            sh "docker-compose run -e CODACY_PROJECT_TOKEN=${env.CODACY_PROJECT_TS_AUTH_LIB_TOKEN} tox"
            junit 'test_results/results.xml'
            sh 'docker-compose down'
        }
    } catch (err) {
        junit 'test_results/results.xml'
        error 'Thunderstorm Client Staging build failed ${err}'

    } finally {
        sh 'docker-compose down'
    }
}
