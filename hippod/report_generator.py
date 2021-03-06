import os
import shutil
import markdown
import tempfile
import datetime
import json
import re
import tempfile
import logging
import glob

import hippod.api_shared
import hippod.error_object

log = logging.getLogger()


class ReportGenerator(object):
    LAST_ACHIEVEMENTS = 1
    FILTER_BY_ANCHOR = 2
    FILTER_BY_CHOICE = 3
    PDF = 4

    @staticmethod
    def generate(app, outputs, report_filter, report_meta):
        reports_path = app['REPORT_PATH']
        tmp_path = os.path.join(app['DB_ROOT_PATH'], 'tmp')
        if not os.path.isdir(tmp_path):
            os.mkdir(tmp_path)
        list_of_lists = ReportGenerator.ReportGeneratorCollector.search(app, report_filter, report_meta)
        date = str(datetime.datetime.now().replace(second=0, microsecond=0).isoformat(sep='-'))
        doc_name = '{}-report.pdf'.format(date)
        pdf_out_path = os.path.join(reports_path, doc_name)
        rpd = ReportGenerator.ReportGeneratorDocument(list_of_lists, tmp_path)
        stored_data = rpd.store_data_in_tmp(app)
        rpd.generate_pdf(app, pdf_out_path, stored_data)


    class ReportGeneratorDocument(object):
        def __init__(self, list_of_lists, tmp_path):
            self.list_of_lists = list_of_lists
            # self.tmp_path = tempfile.TemporaryFile()
            self.tmp_path = tmp_path


        # def __del__(self):
        #     shutil.rmtree(self.tmp_path)

        def get_format_snippet(app, data_id):
            db_path = app['DB_DATA_PATH']
            attr_path = os.path.join(db_path, data_id, 'attr.db')
            with open(attr_path, 'r') as f:
                content = json.load(f)
                snippet_format = content['mime-type'].split('-')[-1]
            return snippet_format


        def get_dst_path(self, data_type, sub_dir, name):
            if data_type == '.png':
                dst_path = os.path.join(sub_dir, '{}.png'.format(name))
            elif data_type == '.jpg':
                dst_path = os.path.join(sub_dir, '{}.jpg'.format(name))
            elif data_type == '.jpeg':
                dst_path = os.path.join(sub_dir, '{}.jpeg'.format(name))
            elif data_type == '.gif':
                dst_path = os.path.join(sub_dir, '{}.gif'.format(name))
            else:
                # FIXME: not sure, but this function should return. If
                # not dst_path is undefined and will definitly crash some
                # lines later!
                log.error("data type not supported: {}".format(data_type))
                return None
            return dst_path


        def copy_to_dst(self, src_path, dst_path):
            with open(src_path, 'rb') as file:
                data = file.read()
                decoded = hippod.hasher.decode_base64_data(data)
            with open(dst_path, 'wb') as file:
                file.write(decoded)
            with open(dst_path, 'wb') as dst:
                shutil.copyfile(src_path, dst_path)


        def store_data(self, app, data, sub_dir):
            src_path = os.path.join(app['DB_DATA_PATH'], data['data-id'], 'blob.bin')
            src_path_snippet = os.path.join(app['DB_SNIPPET_PATH'], '{}.png'.format(data['data-id']))
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)
            # check whether data is a image or description or snippet
            if 'type' not in data:
                head, tail = os.path.split(data['name'])
                name, data_type = os.path.splitext(tail)

                dst_path = self.get_dst_path(data_type, sub_dir, name)
                if not dst_path:
                    return None
                self.copy_to_dst(src_path, dst_path)

            elif data['type'] == 'description':
                dst_path = os.path.join(sub_dir, 'description.md')
                with open(dst_path, 'wb') as dst:
                    shutil.copyfile(src_path, dst_path)

            elif data['type'] == 'snippet':
            # in case of snippet root of src is snippet_db
                if 'name' in data:
                    head, tail = os.path.split(data['name'])
                    name, data_type = os.path.splitext(tail)
                else:
                    name = data['data-id']
                    data_type = get_format_snippet(app, data['data-id'])
                src_path = os.path.join(app['DB_SNIPPET_PATH'], '{}{}'.format(data['data-id'], data_type))
                dst_path = self.get_dst_path(data_type, sub_dir, name)
                if not dst_path:
                    return None
                self.copy_to_dst(src_path, dst_path)
            # else:
            #     FIXME: error handling
            return dst_path


        def store_achievement(self, app, achievement_path, sub_dir):
            with open(achievement_path, 'r') as achiev:
                content = json.load(achiev)
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)
            # check whether data is achievement like
            if 'result' in content:
                dst_path = os.path.join(sub_dir, 'achievement.db')
                with open(dst_path, 'w') as dst:
                    content = json.dumps(content, sort_keys=True,indent=4,
                      separators=(',', ': '))
                    dst.write(content)
                return dst_path
            else:
                return None


        def store_attachment(self, app, attachment_path, sub_dir):
            with open(attachment_path, 'r') as attach:
                content = json.load(attach)
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)
            dst_path = os.path.join(sub_dir, 'attachment.db')
            with open(dst_path, 'w') as dst:
                content = json.dumps(content, sort_keys=True,indent=4,
                      separators=(',', ': '))
                dst.write(content)
            return dst_path


        def get_achievement_content(self, achievement_path):
            with open(achievement_path) as achievement:
                content = json.load(achievement)
                return content


        def get_attachment_content(self, attachment_path):
            default_attach = dict()
            default_attach['responsible'] = 'anonymous'
            if not attachment_path:
                return default_attach
            with open(attachment_path) as attach:
                content = json.load(attach)
                return content


        def add_data(self, description_path, file_path):
            with open(description_path, 'r') as file:
                description = file.read()
            with open(description_path, 'w') as file:
                description = str(description) + '\n' + '![image caption here]({})'.format(file_path) + '\n'
                file.write(description)


        def design_description(self, achievement_content, categories, attach_content, title):
            result = achievement_content['result']
            submitter = achievement_content['submitter']
            test_date = achievement_content['test-date']
            categories = categories
            responsible = attach_content['responsible']

            description  = '# {} #\n\n'.format(title)
            description += '-----------------------   ----------\n'
            description += '**Test Result**           {}\n'.format(result)
            description += '**Categories**            {}\n'.format(categories)
            description += '**Submitter**             {}\n'.format(submitter)
            description += '**Responsible**           {}\n'.format(responsible)
            description += '**Test-Date**             {}\n'.format(test_date)
            description += '-----------------------   ----------\n\n'
            for data in achievement_content['data-references']:
                description += '![Description]({})\n\n'.format(data)
            return description


        def add_achievement(self, description_path, achievement_path, title, \
                            achievement_data, attachment_path, categories):
            attach_content = self.get_attachment_content(attachment_path)
            achievement_content = self.get_achievement_content(achievement_path)
            achievement_content['data-references'] = achievement_data
            if description_path == None:
                # remove '/achievement.db' of the path and create a 'description.md' file in this directory
                tmp_item_path = os.path.dirname(achievement_path)
                description_path = os.path.join(tmp_item_path, 'description.md')

                with open(description_path, 'w') as file:
                    descr = self.design_description(achievement_content, categories, attach_content, title)
                    file.write(descr)
                return description_path
            else:
                with open(description_path, 'r') as file:
                    description_only = file.read()
                with open(description_path, 'w') as file:
                    descr = self.design_description(achievement_content, categories, attach_content, title)
                    descr += str(description_only)
                    file.write(descr)
                return description_path


        def sanitize_description(self, description_path):
            with open(description_path, 'r') as input_file:
                descr_lines = input_file.readlines()
            with open(description_path, 'w') as output_file:
                for line in descr_lines:
                    match = re.search(r'^#[#]*', line)
                    p = re.compile(r'(#[#]*)')
                    if match != None:
                        newline = p.sub('{}#'.format(match.group(0)), line)
                        output_file.write(newline)
                    else:
                        output_file.write(line)


        def adjust_image_reference(self, description_path, attach_path, data_type):
            # looks for available references and arrange the path in the refeferences to the images
            # stored in the tmp file, then returns bool whether image is referenced or not
            data_type = data_type.replace(".", "")
            reference_available = False
            head, tail = os.path.split(attach_path)
            with open(description_path, 'r') as input_file:
                in_descr = input_file.readlines()
            with open(description_path, 'w') as output_file:
                # search for 'xxx(xxx.data_type)'
                regex = r'(\()(.*[.]' + '{})'.format(data_type)
                # regex_compile is a pattern which only looks for the part after the caption
                # in the reference
                regex_compile = r'\(.*[.]' + '{}'.format(data_type)
                p = re.compile(regex_compile)
                for line in in_descr:
                    match = re.search(regex, line)
                    if match:
                        # check whether match 'xxx.xxx' is the wanted image data like 'image.png'
                        if match.group(2) == tail:
                            reference_available = True
                            # exchange only the file path in the refernce(after the caption) with the
                            # new tmp file path
                            newline = p.sub('({}'.format(attach_path), line)
                            output_file.write(newline)
                        else:
                            output_file.write(line)
                    else:
                        output_file.write(line)
            return reference_available


        def fetch_data_list_subcontainer(self, subcontainer_path):
            with open(subcontainer_path, 'r') as subc:
                content = json.load(subc)
            if 'data' not in content['object-item'] or len(content['object-item']['data']) == 0:
                return None
            data_list = content['object-item']['data']
            return data_list


        def fetch_data_list_achievement(self, achievement_path):
            with open(achievement_path, 'r') as achievement:
                content = json.load(achievement)
            if 'data' not in content or len(content['data']) == 0:
                return None
            data_list = content['data']
            return data_list


        def store_data_subcontainer(self, app, data_list, sub_dir):
            stored_paths = list()
            for i, data in enumerate(data_list):
                stored_data_path = self.store_data(app, data, sub_dir)
                if stored_data_path == None:
                    continue
                stored_paths.append(stored_data_path)
            return stored_paths


        def store_data_achievement(self, app, data_list, sub_dir):
            stored_paths = list()
            for i, data in enumerate(data_list):
                stored_data_path = self.store_data(app, data, sub_dir)
                if stored_data_path != None:
                    stored_paths.append(stored_data_path)
            return stored_paths


        def store_data_in_tmp(self, app):
            db_path = app['DB_OBJECT_PATH']
            files_catalog = dict()
            for j, item in enumerate(self.list_of_lists):
                sub_dir = os.path.join(self.tmp_path, 'item{}'.format(j))
                files_catalog[sub_dir] = dict()
                files_catalog[sub_dir]['data'] = dict()
                files_catalog[sub_dir]['data']['achievements'] = list()
                files_catalog[sub_dir]['data']['subcontainer'] = list()

                sha_major = item[0]
                sha_minor = item[1]
                achievement_id = item[2]
                title = item[3]
                last_attachment = item[4]
                categories = item[5]


                files_catalog[sub_dir]['title'] = title
                files_catalog[sub_dir]['categories'] = categories
                
                subcontainer = os.path.join(db_path, sha_major[0:2], sha_major, sha_minor, 'subcontainer.db')
                achievement = os.path.join(db_path, sha_major[0:2], sha_major, sha_minor, 'achievements', '{}.db'.format(achievement_id))

                if not last_attachment:
                    files_catalog[sub_dir]['attachment'] = None
                else:
                    attachment = os.path.join(db_path, sha_major[0:2], sha_major, 'attachments', last_attachment)
                    stored_data_path = self.store_attachment(app, attachment, sub_dir)
                    files_catalog[sub_dir]['attachment'] = stored_data_path

                stored_data_path = self.store_achievement(app, achievement, sub_dir)
                files_catalog[sub_dir]['achievement'] = stored_data_path

                data_list_achievement = self.fetch_data_list_achievement(achievement)
                if data_list_achievement != None:
                    stored_paths = self.store_data_achievement(app, data_list_achievement, sub_dir)
                    for path in stored_paths: files_catalog[sub_dir]['data']['achievements'].append(path)

                data_list_subcontainer = self.fetch_data_list_subcontainer(subcontainer)
                if data_list_subcontainer == None:
                    continue
                stored_paths = self.store_data_subcontainer(app, data_list_subcontainer, sub_dir)
                for path in stored_paths: files_catalog[sub_dir]['data']['subcontainer'].append(path)
            return files_catalog


        def _pandoc_generate(self, app, markdown_in_path, pdf_out_path):
            assert(os.path.isfile(markdown_in_path))
            cmd  = "pandoc "
            cmd += "--latex-engine xelatex "
            if "REPORT-PDF-TEMPLATE" in app:
                cmd += "--template {} ".format(app["REPORT-PDF-TEMPLATE"])
            cmd += "--listings "
            cmd += "--toc "
            cmd += "{} ".format(markdown_in_path)
            cmd += " -o \"{}\" ".format(pdf_out_path)
            log.debug("executing: \"{}\"".format(cmd))
            os.system(cmd)


        def generate_pdf(self, app, pdf_out_path, tmp_data):
            sub_reports = list()
            for key, item in tmp_data.items():
                title = item['title']
                categories = item['categories']
                achievement_data = item['data']['achievements']
                attachment_path = item['attachment']
                counter = 0
                for d in item['data']['subcontainer']:
                    counter += 1
                    name, data_type = os.path.splitext(d)
                    if data_type == '.md':
                        self.sanitize_description(d)
                        description_path = d
                        if 'achievement' in item:
                            achievement_path = item['achievement']
                            self.add_achievement(description_path, achievement_path, title, \
                                                achievement_data, attachment_path, categories)
                        counter = 0
                    # if no '.md' found --> use at least title and test result for the report
                    elif counter == len(item['data']['subcontainer']):
                        if 'achievement' in item:
                            achievement_path = item['achievement']
                            description_path = self.add_achievement(None, achievement_path, title, \
                                                    achievement_data, attachment_path, categories)
                    else:
                        continue
                for d in item['data']['subcontainer']:
                    name, data_type = os.path.splitext(d)
                    if data_type == '.png':
                        attach_path = d
                    elif data_type == '.jpg':
                        attach_path = d
                    elif data_type == '.jpeg':
                        attach_path = d
                    elif data_type == '.gif':
                        attach_path = d
                    else:
                        continue
                    ok = self.adjust_image_reference(description_path, attach_path, data_type)
                    if not ok:
                        self.add_data(description_path, attach_path)
                if len(item['data']['subcontainer']) == 0:
                    achievement_path = item['achievement']
                    description_path = self.add_achievement(None, achievement_path, title, \
                                            achievement_data, attachment_path, categories)
                sub_reports.append(description_path)
            for i in range(len(sub_reports) - 1):
                    with open(sub_reports[i+1], 'r') as file2:
                        description2 = file2.read()
                    with open(sub_reports[0], 'r') as file1:
                        description1 = file1.read()
                        description1 = str(description1) + '\n \n \n' + str(description2)
                    with open(sub_reports[0], 'w') as file1:
                        file1.write(description1)
            # FIXME, need arguments
            self._pandoc_generate(app, sub_reports[0], pdf_out_path)
            # shutil.rmtree(self.tmp_path)





    class ReportGeneratorCollector(object):

        @staticmethod
        def null_func(data):
            pass

        @staticmethod
        def search(app, filter_type, filter_meta):
            object_index_data = hippod.api_shared.object_index_read(app)
            if not object_index_data:
                return None
            # maybe specify limit in filter?
            search_list = list()
            # list_sort_func = (null_func(), reversed)[bool(True)]          # here variable reversed instead of hardcoded True
            # for cont in list_sort_func(object_index_data):
            for cont in object_index_data:
                ok, cont_obj = hippod.api_shared.read_cont_obj_by_id(app, cont['object-item-id'])
                if not ok:
                    log.error("cannot read container {} by sha although it's in object-index.db".format(cont['object-item-id']))
                    continue
                title = cont_obj['title']
                categories = cont_obj['categories']
                if filter_type == ReportGenerator.LAST_ACHIEVEMENTS:
                    last_achiev_list = ReportGenerator.ReportGeneratorCollector.search_last_achievements(app, cont['object-item-id'], cont_obj)
                    last_attach = ReportGenerator.ReportGeneratorCollector.search_last_attachment(app, cont['object-item-id'])
                    last_achiev_list.append(title)
                    last_achiev_list.append(last_attach)
                    last_achiev_list.append(categories)
                    search_list.append(last_achiev_list)
                elif filter_type == ReportGenerator.FILTER_BY_ANCHOR:
                    ReportGenerator.ReportGeneratorCollector.search_anchored_achievements(app, cont['object-item-id'], cont_obj)
                elif filter_type == ReportGenerator.FILTER_BY_CHOICE:
                    choiced_achiev_list = ReportGenerator.ReportGeneratorCollector.search_choiced_achievements(app, cont['object-item-id'], cont_obj, filter_meta)
                    if not choiced_achiev_list:
                        continue
                    for sub_list in choiced_achiev_list:
                        last_attach = ReportGenerator.ReportGeneratorCollector.search_last_attachment(app, cont['object-item-id'])
                        # last attachment?
                        sub_list.append(title)
                        sub_list.append(last_attach)
                        sub_list.append(categories)
                        search_list.append(sub_list)
            return search_list


        @staticmethod
        def search_last_achievements(app, sha_major, cont_obj):
            ret_list = list()
            buff_dict = dict()
            # fetch latest subcontainer (subcontainer with latest achievement) and related meta
            for sub_cont in cont_obj['subcontainer-list']:
                sc = sub_cont['sha-minor']
                ok, full_sub_cont = hippod.api_shared.read_subcont_obj_by_id(app, sha_major, sc)
                if not ok:
                    log.error('cannot read subcontainer {}/{} by sha although sha_minor in subcontainer-list'.format(sha_major, sha_minor))
                    continue
                data = hippod.api_object_get_full.get_all_achievement_data(app, sha_major, sc, full_sub_cont)
                if data:
                    buff_dict[sc] = data[0]['date-added']
            if data:
                latest_sha_minor = max(buff_dict, key=lambda key: buff_dict[key])
                latest_index = next(index for (index,d) in enumerate(cont_obj['subcontainer-list']) if d['sha-minor'] == latest_sha_minor)

            ret_list.append(sha_major)

            if not data:
                sub_cont_last = cont_obj['subcontainer-list'][0]
                latest_sha_minor = sub_cont_last['sha-minor']
            else:
                sub_cont_last = cont_obj['subcontainer-list'][latest_index]
            ret_list.append(sub_cont_last['sha-minor'])

            db_root_path = app['DB_OBJECT_PATH']
            subcntr_path = os.path.join(db_root_path, sha_major[0:2], sha_major,\
                                        latest_sha_minor, 'subcontainer.db')
            with open(subcntr_path) as file:
                full_sub_cont_last = json.load(file)

            data = hippod.api_object_get_detail.get_last_achievement_data(app, sha_major, latest_sha_minor, full_sub_cont_last)
            ret_list.append(data['id'])
            return ret_list


        @staticmethod
        def search_choiced_achievements(app, sha_major, cont_obj, filter_meta):
            ret_list = list()
            if 'anchors' in filter_meta:
                anchors_filter = filter_meta['anchors']
            if 'submitter' in filter_meta:
                submitter_filter = filter_meta['submitter']
            # FIXME: multiple entries shouldn't be in the ret_list!
            for sub_cont in cont_obj['subcontainer-list']:
                sub_ret_list = list()
                sha_minor = sub_cont['sha-minor']
                ok, full_sub_cont = hippod.api_shared.read_subcont_obj_by_id(app, sha_major, sha_minor)
                achievements = full_sub_cont['achievements']
                achievement_data_list = hippod.api_object_get_full.get_all_achievement_data(app, sha_major, sha_minor, full_sub_cont)
                for achievement in achievement_data_list:
                    sub_ret_list1 = list()
                    submitter = achievement['submitter']
                    if 'anchors' in filter_meta and 'submitter' in filter_meta:
                        if 'anchor' in achievement:
                            anchor = achievement['anchor']
                            if submitter in submitter_filter and anchor in anchors_filter:
                                sub_ret_list1.append(sha_major)
                                sub_ret_list1.append(sha_minor)
                                sub_ret_list1.append(str(achievement['id']))
                            else:
                                continue
                        else:
                            continue
                    elif 'anchors' in filter_meta:
                        if 'anchor' in achievement:
                            anchor = achievement['anchor']
                            if anchor in anchors_filter:
                                sub_ret_list1.append(sha_major)
                                sub_ret_list1.append(sha_minor)
                                sub_ret_list1.append(str(achievement['id']))
                            else:
                                continue
                        else:
                            continue
                    elif 'submitter' in filter_meta and submitter in submitter_filter:
                        sub_ret_list1.append(sha_major)
                        sub_ret_list1.append(sha_minor)
                        sub_ret_list1.append(str(achievement['id']))
                    else:
                        continue
                    sub_ret_list.append(sub_ret_list1)
                for sub in sub_ret_list:
                    ret_list.append(sub)
            return ret_list


        @staticmethod
        def search_anchored_achievements(app, sha_major, cont_obj):
            pass


        @staticmethod
        def search_last_attachment(app, sha_major):
            obj_path = os.path.join(app['DB_OBJECT_PATH'])
            attach_path = os.path.join(obj_path, sha_major[0:2], sha_major, 'attachments')
            attach_files = os.path.join(attach_path, '*')
            attach_list = glob.glob(attach_files)
            if len(attach_list) == 0:
                return None
            last_attach = max(attach_list, key=os.path.getctime)
            return last_attach