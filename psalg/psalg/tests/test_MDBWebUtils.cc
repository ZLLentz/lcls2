/* 
 * https://curl.haxx.se/libcurl/c/getinfo.html
 */

#include "psalg/utils/Logger.hh" // MSG, LOGGER,...

#include <stdio.h>
#include <iostream>

//#define CURL_STATICLIB
#include <curl/curl.h>
#include <curl/easy.h>

#include "psalg/calib/MDBWebUtils.hh"

using namespace psalg;

//-------------------

void print_hline(const uint nchars, const char c) {printf("%s\n", std::string(nchars,c).c_str());}

//-------------------

int test_getinfo(void) {
  printf("In test_getinfo\n");

  CURL *curl = curl_easy_init();
  if(curl) {
    //curl_easy_setopt(curl, CURLOPT_URL, "http://example.com");
    curl_easy_setopt(curl, CURLOPT_URL, "https://pswww-dev.slac.stanford.edu/calib_ws"); // .edu:9306
    CURLcode res = curl_easy_perform(curl);
 
    if(CURLE_OK == res) {
      char *ct;
      // ask for the content-type
      res = curl_easy_getinfo(curl, CURLINFO_CONTENT_TYPE, &ct);
 
      if((CURLE_OK == res) && ct)
        printf("\nWe received Content-Type: %s\n", ct);
    }
 
    // always cleanup
    curl_easy_cleanup(curl);
  }

  return 0;
}

//-------------------
 
void test_request() {
  printf("In test_request\n");
  request(); // (const char* url=URL, const char* query="");
  const std::string& s = string_response();
  std::cout << "XXX resp: " << s << '\n';
}

//-------------------
 
void test_database_names() {
  printf("In database_names\n");
  const std::vector<std::string>& v = database_names();
  //const std::string& s = string_response();
  //std::cout << "XXX resp: " << s << '\n';
  print_vector_of_strings(v);
}

//-------------------
 
void test_collection_names() {
  printf("In test_collection_names\n");
  const std::vector<std::string>& v = collection_names("cdb_cspad_0001");
  //const std::string& s = string_response();
  //std::cout << "XXX resp: " << s << '\n';
  print_vector_of_strings(v);
}

//-------------------

int main(void)
{
  //MSG(INFO, LOGGER.tstampStart() << " Logger started"); // optional record
  LOGGER.setLogger(LL::DEBUG, "%H:%M:%S.%f");           // set level and time format
  printf("In test_MDBWebUtils\n");
  print_hline(80,'_');
  //test_getinfo(); print_hline(80,'_');
  test_request(); print_hline(80,'_');
  test_database_names(); print_hline(80,'_');
  test_collection_names(); print_hline(80,'_');
}

//-------------------

