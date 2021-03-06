# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

DYNAMIC_HOST_SET_SOURCES = set([ 'pool/DynamicHostSet.java' ])

URL_RESOLVER_SOURCES = set([
  'UrlResolver.java',
  'UrlResolverUtil.java'
])

java_library(name = 'dynamic-host-set',
  provides = artifact(
    org = 'com.twitter.common',
    name = 'dynamic-host-set',
    repo = pants('build-support/commons/ivy:public'),
  ),
  dependencies = [
    pants('3rdparty/jvm/com/google/guava'),
    pants('src/java/com/twitter/common/base'),
  ],
  sources = DYNAMIC_HOST_SET_SOURCES
)

java_library(name = 'util',
  provides = artifact(
    org = 'com.twitter.common',
    name = 'net-util',
    repo = pants('build-support/commons/ivy:public'),
  ),
  dependencies = [
    pants('3rdparty/jvm/commons-codec'),
    pants('3rdparty/jvm/commons-lang'),
    pants('3rdparty/jvm/com/google/guava'),
    pants('src/java/com/twitter/common/base'),
    pants('src/java/com/twitter/common/collections'),
  ],
  sources = globs('*.java') - URL_RESOLVER_SOURCES
)

java_library(name = 'url-resolver',
  dependencies = [
    pants('3rdparty/jvm/com/google/guava'),
    pants('3rdparty/jvm/com/google/code/findbugs:jsr305'),
    pants(':util'),
    pants('src/java/com/twitter/common/base'),
    pants('src/java/com/twitter/common/quantity'),
    pants('src/java/com/twitter/common/stats:util'),
    pants('src/java/com/twitter/common/util'),
    pants('src/java/com/twitter/common/util/caching'),
  ],
  sources = URL_RESOLVER_SOURCES
)

# TODO(John Sirois): tease apart loadbalancing/monitoring/pool
java_library(name = 'pool',
  provides = artifact(
    org = 'com.twitter.common',
    name = 'net-pool',
    repo = pants('build-support/commons/ivy:public'),
  ),
  dependencies = [
    pants('3rdparty/jvm/commons-codec'),
    pants('3rdparty/jvm/com/google/guava'),
    pants('3rdparty/jvm/com/google/code/findbugs:jsr305'),
    pants(':dynamic-host-set'),
    pants('src/java/com/twitter/common/base'),
    pants('src/java/com/twitter/common/quantity'),
    pants('src/java/com/twitter/common/stats'),
    pants('src/java/com/twitter/common/util'),
    pants('src/java/com/twitter/common/util:system-mocks'),
  ],
  sources = globs('pool/*.java', 'monitoring/*.java', 'loadbalancing/*.java')
    - DYNAMIC_HOST_SET_SOURCES
)
