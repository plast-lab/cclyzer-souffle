#ifndef CSV_WRITER_H__
#define CSV_WRITER_H__

#include <cstdint>
#include <sstream>
#include <string>
#include <unordered_set>
#include <boost/filesystem.hpp>
#include <boost/filesystem/fstream.hpp>

namespace cclyzer {

    // Define serializable type trait. Only serializable types will be
    // allowed to be written by CSV writer
    template<class T>
    struct is_serializable
        : std::integral_constant<
        bool,
        std::is_convertible<T, const char*>::value ||
        std::is_arithmetic<T>::value ||
        std::is_same<std::string, typename std::remove_cv<T>::type>::value
        >
    {};

    // Define variadic serializable type trait that generalizes to
    // multiple values
    template <typename... Ts>
    struct all_serializable;

    template <typename Head, typename... Tail>
    struct all_serializable<Head, Tail...>
    {
        static const bool value =
            is_serializable<Head>::value && all_serializable<Tail...>::value;
    };

    template <typename T>
    struct all_serializable<T>
    {
        static const bool value = is_serializable<T>::value;
    };


    //-----------------------------------------------------------------------
    // Generic CSV writer class
    //-----------------------------------------------------------------------

    class csv_writer
    {
      public:

        typedef boost::filesystem::path path;
        typedef boost::filesystem::ofstream ofstream;

        /* Constructor must create output file stream */

        csv_writer(const path& csvfile, std::string delimiter = "\t")
            : out(csvfile), delim(delimiter)
        {
            // Create parent directory
            create_directory(csvfile.parent_path());
        }

        /* Destructor must flush and close underlying file stream */
        ~csv_writer() {
            out.flush();
            out.close();
        }


        /* Basic routines for appending new records to CSV files.
         * Each distinct record is written once: callers may emit the same
         * fact several times (e.g. once per use), and the files stay sets. */

        void write(const std::string& hdr) {
            emit(hdr);
        }


        template<typename V, typename... Vs>
        void write(const std::string& hdr, const V& fld, const Vs&... flds)
        {
            static_assert( all_serializable<V, Vs...>::value,
                           "All types must be serializable" );
            std::ostringstream row;
            row << hdr;
            appendFields(row, fld, flds...);
            emit(row.str());
        }

      protected:

        /* Variadic method to append fields to record */

        void appendFields(std::ostream&) {}

        template<typename V, typename ...Vargs>
        void appendFields(std::ostream& os, const V& value) {
            os << delim << value;
        }

        template<typename V, typename ...Vs>
        void appendFields(std::ostream& os, const V& value, const Vs&... values) {
            appendFields(os, value);
            appendFields(os, values...);
        }

      private:

        /* 128-bit fingerprint of a record (two independent 64-bit hashes),
         * so remembering what was written costs 16 bytes per record. */
        struct fingerprint {
            std::uint64_t a, b;
            bool operator==(const fingerprint& o) const { return a == o.a && b == o.b; }
        };
        struct fingerprint_hash {
            std::size_t operator()(const fingerprint& f) const { return f.a ^ (f.b * 0x9e3779b97f4a7c15ULL); }
        };

        static fingerprint fingerprint_of(const std::string& row) {
            std::uint64_t fnv = 0xcbf29ce484222325ULL;          // FNV-1a
            for (unsigned char c : row) { fnv ^= c; fnv *= 0x100000001b3ULL; }
            return { std::hash<std::string>{}(row), fnv };
        }

        void emit(const std::string& row) {
            if (seen.insert(fingerprint_of(row)).second)
                out << row << "\n";
        }

        std::unordered_set<fingerprint, fingerprint_hash> seen;

      private:

        /* CSV Output Stream */
        ofstream out;

        /* Column Delimiter */
        const std::string delim;
    };

} // end of namespace cclyzer

#endif /* CSV_WRITER_H__ */
