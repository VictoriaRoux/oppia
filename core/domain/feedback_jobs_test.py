# coding: utf-8
#
# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for continuous computations relating to feedback analytics."""

from core import jobs_registry
from core.domain import feedback_jobs
from core.platform import models
(feedback_models,) = models.Registry.import_models([models.NAMES.feedback])
from core.tests import test_utils


class ModifiedFeedbackAnalyticsAggregator(
        feedback_jobs.FeedbackAnalyticsAggregator):
    """A modified FeedbackAnalyticsAggregator that does not start a new batch
    job when the previous one has finished.
    """
    @classmethod
    def _get_batch_job_manager_class(cls):
        return ModifiedFeedbackAnalyticsMRJobManager

    @classmethod
    def _kickoff_batch_job_after_previous_one_ends(cls):
        pass


class ModifiedFeedbackAnalyticsMRJobManager(
        feedback_jobs.FeedbackAnalyticsMRJobManager):

    @classmethod
    def _get_continuous_computation_class(cls):
        return ModifiedFeedbackAnalyticsAggregator


class FeedbackAnalyticsAggregatorUnitTests(test_utils.GenericTestBase):
    """Tests for statistics aggregations."""

    ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS = [
        ModifiedFeedbackAnalyticsAggregator]

    def test_no_threads(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            exp_id = 'eid'
            self.save_new_valid_exploration(exp_id, 'owner')

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 0,
                'num_total_threads': 0,
            })

    def test_single_thread_single_exp(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            exp_id = 'eid'
            thread_id = 'tid'
            self.save_new_valid_exploration(exp_id, 'owner')
            thread = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id)
            thread.exploration_id = exp_id
            thread.put()

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 1,
                'num_total_threads': 1,
            })

    def test_multiple_threads_single_exp(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            exp_id = 'eid'
            thread_id_1 = 'tid1'
            thread_id_2 = 'tid2'
            self.save_new_valid_exploration(exp_id, 'owner')
            thread_1 = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_1)
            thread_1.exploration_id = exp_id
            thread_1.put()
            thread_2 = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_2)
            thread_2.exploration_id = exp_id
            thread_2.put()

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 2,
                'num_total_threads': 2,
            })

    def test_multiple_threads_multiple_exp(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            exp_id_1 = 'eid1'
            exp_id_2 = 'eid2'
            thread_id_1 = 'tid1'
            thread_id_2 = 'tid2'
            thread_id_3 = 'tid3'
            thread_id_4 = 'tid4'
            self.save_new_valid_exploration(exp_id_1, 'owner')
            self.save_new_valid_exploration(exp_id_2, 'owner')
            thread_1 = feedback_models.FeedbackThreadModel.create(
                exp_id_1, thread_id_1)
            thread_1.exploration_id = exp_id_1
            thread_1.put()
            thread_2 = feedback_models.FeedbackThreadModel.create(
                exp_id_1, thread_id_2)
            thread_2.exploration_id = exp_id_1
            thread_2.put()
            thread_3 = feedback_models.FeedbackThreadModel.create(
                exp_id_2, thread_id_3)
            thread_3.exploration_id = exp_id_2
            thread_3.put()
            thread_4 = feedback_models.FeedbackThreadModel.create(
                exp_id_2, thread_id_4)
            thread_4.exploration_id = exp_id_2
            thread_4.put()

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id_1), {
                'num_open_threads': 2,
                'num_total_threads': 2,
            })
            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id_2), {
                'num_open_threads': 2,
                'num_total_threads': 2,
            })

    def test_thread_closed_job_running(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            user_id = 'uid'
            exp_id = 'eid'
            thread_id_1 = 'tid1'
            self.save_new_valid_exploration(exp_id, 'owner')
            thread_1 = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_1)
            thread_1.exploration_id = exp_id
            thread_1.put()

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 1,
                'num_total_threads': 1,
            })

            # Stop job.
            ModifiedFeedbackAnalyticsAggregator.stop_computation(user_id)
            self.assertEqual(self.count_jobs_in_taskqueue(), 0)

            # Close thread.
            thread = (feedback_models.FeedbackThreadModel.
                      get_by_exp_and_thread_id(exp_id, thread_id_1))
            thread.status = feedback_models.STATUS_CHOICES_FIXED
            thread.put()

            # Restart job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 0,
                'num_total_threads': 1,
            })

    def test_thread_closed_reopened_again(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            user_id = 'uid'
            exp_id = 'eid'
            thread_id_1 = 'tid1'
            self.save_new_valid_exploration(exp_id, 'owner')
            thread_1 = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_1)
            thread_1.exploration_id = exp_id
            thread_1.put()

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 1,
                'num_total_threads': 1,
            })

            # Stop job.
            ModifiedFeedbackAnalyticsAggregator.stop_computation(user_id)
            self.assertEqual(self.count_jobs_in_taskqueue(), 0)

            # Close thread.
            thread = (feedback_models.FeedbackThreadModel.
                      get_by_exp_and_thread_id(exp_id, thread_id_1))
            thread.status = feedback_models.STATUS_CHOICES_FIXED
            thread.put()

            # Restart job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 0,
                'num_total_threads': 1,
            })

            # Stop job.
            ModifiedFeedbackAnalyticsAggregator.stop_computation(user_id)
            self.assertEqual(self.count_jobs_in_taskqueue(), 0)

            # Reopen thread.
            thread = (feedback_models.FeedbackThreadModel.
                      get_by_exp_and_thread_id(exp_id, thread_id_1))
            thread.status = feedback_models.STATUS_CHOICES_OPEN
            thread.put()

            # Restart job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 1,
                'num_total_threads': 1,
            })

    def test_thread_closed_status_changed(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            user_id = 'uid'
            exp_id = 'eid'
            thread_id_1 = 'tid1'
            self.save_new_valid_exploration(exp_id, 'owner')
            thread_1 = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_1)
            thread_1.exploration_id = exp_id
            thread_1.put()

            # Start job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 1,
                'num_total_threads': 1,
            })

            # Stop job.
            ModifiedFeedbackAnalyticsAggregator.stop_computation(user_id)
            self.assertEqual(self.count_jobs_in_taskqueue(), 0)

            # Close thread.
            thread = (feedback_models.FeedbackThreadModel.
                      get_by_exp_and_thread_id(exp_id, thread_id_1))
            thread.status = feedback_models.STATUS_CHOICES_FIXED
            thread.put()

            # Restart job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 0,
                'num_total_threads': 1,
            })

            # Stop job.
            ModifiedFeedbackAnalyticsAggregator.stop_computation(user_id)
            self.assertEqual(self.count_jobs_in_taskqueue(), 0)

            # Change thread status.
            thread = (feedback_models.FeedbackThreadModel.
                      get_by_exp_and_thread_id(exp_id, thread_id_1))
            thread.status = feedback_models.STATUS_CHOICES_IGNORED
            thread.put()

            # Restart job.
            self.process_and_flush_pending_tasks()
            ModifiedFeedbackAnalyticsAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            self.assertEqual(
                ModifiedFeedbackAnalyticsAggregator.get_thread_analytics(
                    exp_id), {
                'num_open_threads': 0,
                'num_total_threads': 1,
            })
