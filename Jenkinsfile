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

        // determine if release should be pushed: the most recent commit must contain string "[release]"
        def is_release = sh (script: 'git log --oneline --no-merges -1 | grep -q \'\\[release\\]\'', returnStatus: true)

        // master branch builds are pushed to Github
        if (env.BRANCH_NAME == 'master') {
            stage('Create Github Release') {
                if (is_release == 0) {
                    // extract application version
                    def version = sh (script: 'python setup.py --version', returnStdout: true)

                    // GITHUB_TOKEN is a global set in jenkins
                    withEnv([
                        "GITHUB_TOKEN=${env.GITHUB_TOKEN}",
                    ]) {
                        sh "make release"
                    }
                } else {
                    echo 'No [release] commit -- skipping'
                }
            }
      }
    } catch (err) {
        junit 'test_results/results.xml'
        error 'Thunderstorm Client Staging build failed ${err}'

    } finally {
        sh 'docker-compose down'
    }
}
